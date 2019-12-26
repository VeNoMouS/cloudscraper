import logging
import re
import sys
import ssl
import requests

try:
    import copyreg
except ImportError:
    import copy_reg as copyreg

from copy import deepcopy
from time import sleep
from collections import OrderedDict

from requests.sessions import Session
from requests.adapters import HTTPAdapter

from .interpreters import JavaScriptInterpreter
from .reCaptcha import reCaptcha
from .user_agent import User_Agent

try:
    from requests_toolbelt.utils import dump
except ImportError:
    pass

try:
    import brotli
except ImportError:
    pass

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

# ------------------------------------------------------------------------------- #

__version__ = '1.2.19'

# ------------------------------------------------------------------------------- #


class CipherSuiteAdapter(HTTPAdapter):

    __attrs__ = [
        'ssl_context',
        'max_retries',
        'config',
        '_pool_connections',
        '_pool_maxsize',
        '_pool_block'
    ]

    def __init__(self, *args, **kwargs):
        self.ssl_context = kwargs.pop('ssl_context', None)
        self.cipherSuite = kwargs.pop('cipherSuite', None)

        if not self.ssl_context:
            self.ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            self.ssl_context.set_ciphers(self.cipherSuite)
            self.ssl_context.options |= (ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1)

        super(CipherSuiteAdapter, self).__init__(**kwargs)

    # ------------------------------------------------------------------------------- #

    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_context'] = self.ssl_context
        return super(CipherSuiteAdapter, self).init_poolmanager(*args, **kwargs)

    # ------------------------------------------------------------------------------- #

    def proxy_manager_for(self, *args, **kwargs):
        kwargs['ssl_context'] = self.ssl_context
        return super(CipherSuiteAdapter, self).proxy_manager_for(*args, **kwargs)

# ------------------------------------------------------------------------------- #


class CloudScraper(Session):

    def __init__(self, *args, **kwargs):
        self.debug = kwargs.pop('debug', False)
        self.delay = kwargs.pop('delay', None)
        self.cipherSuite = kwargs.pop('cipherSuite', None)
        self.interpreter = kwargs.pop('interpreter', 'native')
        self.recaptcha = kwargs.pop('recaptcha', {})
        self.allow_brotli = kwargs.pop(
            'allow_brotli',
            True if 'brotli' in sys.modules.keys() else False
        )
        self.user_agent = User_Agent(
            allow_brotli=self.allow_brotli,
            browser=kwargs.pop('browser', None)
        )

        self._solveDepthCnt = 0
        self.solveDepth = kwargs.pop('solveDepth', 3)

        super(CloudScraper, self).__init__(*args, **kwargs)

        # pylint: disable=E0203
        if 'requests' in self.headers['User-Agent']:
            # ------------------------------------------------------------------------------- #
            # Set a random User-Agent if no custom User-Agent has been set
            # ------------------------------------------------------------------------------- #
            self.headers = self.user_agent.headers

        self.mount(
            'https://',
            CipherSuiteAdapter(
                cipherSuite=':'.join(self.user_agent.cipherSuite)
                if not self.cipherSuite else ':'.join(self.cipherSuite)
                if isinstance(self.cipherSuite, list) else self.cipherSuite
            )
        )

        # purely to allow us to pickle dump
        copyreg.pickle(ssl.SSLContext, lambda obj: (obj.__class__, (obj.protocol,)))

    # ------------------------------------------------------------------------------- #
    # Allow us to pickle our session back with all variables
    # ------------------------------------------------------------------------------- #

    def __getstate__(self):
        return self.__dict__

    # ------------------------------------------------------------------------------- #
    # debug the request via the response
    # ------------------------------------------------------------------------------- #

    @staticmethod
    def debugRequest(req):
        try:
            print(dump.dump_all(req).decode('utf-8'))
        except ValueError as e:
            print("Debug Error: {}".format(getattr(e, 'message', e)))

    # ------------------------------------------------------------------------------- #
    # Decode Brotli on older versions of urllib3 manually
    # ------------------------------------------------------------------------------- #

    def decodeBrotli(self, resp):
        if requests.packages.urllib3.__version__ < '1.25.1' and resp.headers.get('Content-Encoding') == 'br':
            if self.allow_brotli and resp._content:
                resp._content = brotli.decompress(resp.content)
            else:
                logging.warning(
                    'You\'re running urllib3 {}, Brotli content detected, '
                    'Which requires manual decompression, '
                    'But option allow_brotli is set to False, '
                    'We will not continue to decompress.'.format(requests.packages.urllib3.__version__)
                )

        return resp

    # ------------------------------------------------------------------------------- #
    # Our hijacker request function
    # ------------------------------------------------------------------------------- #

    def request(self, method, url, *args, **kwargs):
        # pylint: disable=E0203
        if kwargs.get('proxies') and kwargs.get('proxies') != self.proxies:
            self.proxies = kwargs.get('proxies')

        resp = self.decodeBrotli(
            super(CloudScraper, self).request(method, url, *args, **kwargs)
        )

        # ------------------------------------------------------------------------------- #
        # Debug request
        # ------------------------------------------------------------------------------- #

        if self.debug:
            self.debugRequest(resp)

        # Check if Cloudflare anti-bot is on
        if self.is_Challenge_Request(resp):
            # ------------------------------------------------------------------------------- #
            # Try to solve the challenge and send it back
            # ------------------------------------------------------------------------------- #

            if self._solveDepthCnt >= self.solveDepth:
                sys.tracebacklimit = 0
                _ = self._solveDepthCnt
                self._solveDepthCnt = 0
                raise RuntimeError(
                    "!!Loop Protection!! We have tried to solve {} time(s) in a row.".format(_)
                )

            self._solveDepthCnt += 1

            resp = self.Challenge_Response(resp, **kwargs)
        else:
            if not resp.is_redirect and resp.status_code not in [429, 503]:
                self._solveDepthCnt = 0

        return resp

    # ------------------------------------------------------------------------------- #
    # check if the response contains a valid Cloudflare challenge
    # ------------------------------------------------------------------------------- #

    @staticmethod
    def is_IUAM_Challenge(resp):
        try:
            return (
                resp.headers.get('Server', '').startswith('cloudflare')
                and resp.status_code in [429, 503]
                and re.search(
                    r'action="/.*?__cf_chl_jschl_tk__=\S+".*?name="jschl_vc"\svalue=.*?',
                    resp.text,
                    re.M | re.DOTALL
                )
            )
        except AttributeError:
            pass

        return False

    # ------------------------------------------------------------------------------- #
    # check if the response contains a valid Cloudflare reCaptcha challenge
    # ------------------------------------------------------------------------------- #

    @staticmethod
    def is_reCaptcha_Challenge(resp):
        try:
            return (
                resp.headers.get('Server', '').startswith('cloudflare')
                and resp.status_code == 403
                and re.search(
                    r'action="/.*?__cf_chl_captcha_tk__=\S+".*?data\-sitekey=.*?',
                    resp.text,
                    re.M | re.DOTALL
                )
            )
        except AttributeError:
            pass

        return False

    # ------------------------------------------------------------------------------- #
    # check if the response contains Firewall 1020 Error
    # ------------------------------------------------------------------------------- #

    @staticmethod
    def is_Firewall_Blocked(resp):
        try:
            return (
                resp.headers.get('Server', '').startswith('cloudflare')
                and resp.status_code == 403
                and re.search(
                    r'<span class="cf-error-code">1020</span>',
                    resp.text,
                    re.M | re.DOTALL
                )
            )
        except AttributeError:
            pass

        return False

    # ------------------------------------------------------------------------------- #
    # Wrapper for is_reCaptcha_Challenge, is_IUAM_Challenge, is_Firewall_Blocked
    # ------------------------------------------------------------------------------- #

    def is_Challenge_Request(self, resp):
        if self.is_Firewall_Blocked(resp):
            sys.tracebacklimit = 0
            raise RuntimeError('Cloudflare has blocked this request (Code 1020 Detected).')

        if self.is_reCaptcha_Challenge(resp) or self.is_IUAM_Challenge(resp):
            return True

        return False

    # ------------------------------------------------------------------------------- #
    # Try to solve cloudflare javascript challenge.
    # ------------------------------------------------------------------------------- #

    @staticmethod
    def IUAM_Challenge_Response(body, url, interpreter):
        try:
            challengeUUID = re.search(
                r'id="challenge-form" action="(?P<challengeUUID>\S+)"',
                body, re.M | re.DOTALL
            ).groupdict().get('challengeUUID', '')
            payload = OrderedDict(re.findall(r'name="(r|jschl_vc|pass)"\svalue="(.*?)"', body))
        except AttributeError:
            sys.tracebacklimit = 0
            raise RuntimeError(
                "Cloudflare IUAM detected, unfortunately we can't extract the parameters correctly."
            )

        hostParsed = urlparse(url)

        try:
            payload['jschl_answer'] = JavaScriptInterpreter.dynamicImport(
                interpreter
            ).solveChallenge(body, hostParsed.netloc)
        except Exception as e:
            raise RuntimeError(
                'Unable to parse Cloudflare anti-bots page: {}'.format(
                    getattr(e, 'message', e)
                )
            )

        return {
            'url': '{}://{}{}'.format(
                hostParsed.scheme,
                hostParsed.netloc,
                challengeUUID
            ),
            'data': payload
        }

    # ------------------------------------------------------------------------------- #
    #  Try to solve the reCaptcha challenge via 3rd party.
    # ------------------------------------------------------------------------------- #

    @staticmethod
    def reCaptcha_Challenge_Response(provider, provider_params, body, url):
        try:
            payload = re.search(
                r'(name="r"\svalue="(?P<r>\S+)"|).*?challenge-form" action="(?P<challengeUUID>\S+)".*?'
                r'data-ray="(?P<data_ray>\S+)".*?data-sitekey="(?P<site_key>\S+)"',
                body, re.M | re.DOTALL
            ).groupdict()
        except (AttributeError):
            sys.tracebacklimit = 0
            raise RuntimeError(
                "Cloudflare reCaptcha detected, unfortunately we can't extract the parameters correctly."
            )

        hostParsed = urlparse(url)
        return {
            'url': '{}://{}{}'.format(
                hostParsed.scheme,
                hostParsed.netloc,
                payload.get('challengeUUID', '')
            ),
            'data': OrderedDict([
                ('r', payload.get('r', '')),
                ('id', payload.get('data_ray')),
                (
                    'g-recaptcha-response',
                    reCaptcha.dynamicImport(
                        provider.lower()
                    ).solveCaptcha(url, payload.get('site_key'), provider_params)
                )
            ])
        }

    # ------------------------------------------------------------------------------- #
    # Attempt to handle and send the challenge response back to cloudflare
    # ------------------------------------------------------------------------------- #

    def Challenge_Response(self, resp, **kwargs):
        if self.is_reCaptcha_Challenge(resp):
            # ------------------------------------------------------------------------------- #
            # double down on the request as some websites are only checking
            # if cfuid is populated before issuing reCaptcha.
            # ------------------------------------------------------------------------------- #

            resp = self.decodeBrotli(
                super(CloudScraper, self).request(resp.request.method, resp.url, **kwargs)
            )

            if not self.is_reCaptcha_Challenge(resp):
                return resp

            # ------------------------------------------------------------------------------- #
            # if no reCaptcha provider raise a runtime error.
            # ------------------------------------------------------------------------------- #

            if not self.recaptcha or not isinstance(self.recaptcha, dict) or not self.recaptcha.get('provider'):
                sys.tracebacklimit = 0
                raise RuntimeError(
                    "Cloudflare reCaptcha detected, unfortunately you haven't loaded an anti reCaptcha provider "
                    "correctly via the 'recaptcha' parameter."
                )

            # ------------------------------------------------------------------------------- #
            # if provider is return_response, return the response without doing anything.
            # ------------------------------------------------------------------------------- #

            if self.recaptcha.get('provider') == 'return_response':
                return resp

            self.recaptcha['proxies'] = self.proxies
            submit_url = self.reCaptcha_Challenge_Response(
                self.recaptcha.get('provider'),
                self.recaptcha,
                resp.text,
                resp.url
            )
        else:
            # ------------------------------------------------------------------------------- #
            # Cloudflare requires a delay before solving the challenge
            # ------------------------------------------------------------------------------- #

            if not self.delay:
                try:
                    delay = float(
                        re.search(
                            r'submit\(\);\r?\n\s*},\s*([0-9]+)',
                            resp.text
                        ).group(1)
                    ) / float(1000)
                    if isinstance(delay, (int, float)):
                        self.delay = delay
                except (AttributeError, ValueError):
                    sys.tracebacklimit = 0
                    raise RuntimeError("Cloudflare IUAM possibility malformed, issue extracing delay value.")

            sleep(self.delay)

            # ------------------------------------------------------------------------------- #

            submit_url = self.IUAM_Challenge_Response(
                resp.text,
                resp.url,
                self.interpreter
            )

        # ------------------------------------------------------------------------------- #
        # Send the Challenge Response back to Cloudflare
        # ------------------------------------------------------------------------------- #

        if submit_url:

            def updateAttr(obj, name, newValue):
                try:
                    obj[name].update(newValue)
                    return obj[name]
                except (AttributeError, KeyError):
                    obj[name] = {}
                    obj[name].update(newValue)
                    return obj[name]

            cloudflare_kwargs = deepcopy(kwargs)
            cloudflare_kwargs['allow_redirects'] = False
            cloudflare_kwargs['data'] = updateAttr(
                cloudflare_kwargs,
                'data',
                submit_url['data']
            )

            urlParsed = urlparse(resp.url)
            cloudflare_kwargs['headers'] = updateAttr(
                cloudflare_kwargs,
                'headers',
                {
                    'Origin': '{}://{}'.format(urlParsed.scheme, urlParsed.netloc),
                    'Referer': resp.url
                }
            )

            challengeSubmitResponse = self.request(
                'POST',
                submit_url['url'],
                **cloudflare_kwargs
            )

            # ------------------------------------------------------------------------------- #
            # Return response if Cloudflare is doing content pass through instead of 3xx
            # else request with redirect URL also handle protocol scheme change http -> https
            # ------------------------------------------------------------------------------- #

            if not challengeSubmitResponse.is_redirect:
                return challengeSubmitResponse
            else:
                cloudflare_kwargs = deepcopy(kwargs)

                if not urlparse(challengeSubmitResponse.headers['Location']).netloc:
                    cloudflare_kwargs['headers'] = updateAttr(
                        cloudflare_kwargs,
                        'headers',
                        {'Referer': '{}://{}'.format(urlParsed.scheme, urlParsed.netloc)}
                    )
                    return self.request(
                        resp.request.method,
                        '{}://{}{}'.format(
                            urlParsed.scheme,
                            urlParsed.netloc,
                            challengeSubmitResponse.headers['Location']
                        ),
                        **cloudflare_kwargs
                    )
                else:
                    redirectParsed = urlparse(challengeSubmitResponse.headers['Location'])
                    cloudflare_kwargs['headers'] = updateAttr(
                        cloudflare_kwargs,
                        'headers',
                        {'Referer': '{}://{}'.format(redirectParsed.scheme, redirectParsed.netloc)}
                    )
                    return self.request(
                        resp.request.method,
                        challengeSubmitResponse.headers['Location'],
                        **cloudflare_kwargs
                    )

        # ------------------------------------------------------------------------------- #
        # We shouldn't be here...
        # Re-request the original query and/or process again....
        # ------------------------------------------------------------------------------- #

        return self.request(resp.request.method, resp.url, **kwargs)
    # ------------------------------------------------------------------------------- #

    @classmethod
    def create_scraper(cls, sess=None, **kwargs):
        """
        Convenience function for creating a ready-to-go CloudScraper object.
        """
        scraper = cls(**kwargs)

        if sess:
            for attr in ['auth', 'cert', 'cookies', 'headers', 'hooks', 'params', 'proxies', 'data']:
                val = getattr(sess, attr, None)
                if val:
                    setattr(scraper, attr, val)

        return scraper

    # ------------------------------------------------------------------------------- #
    # Functions for integrating cloudscraper with other applications and scripts
    # ------------------------------------------------------------------------------- #

    @classmethod
    def get_tokens(cls, url, **kwargs):
        scraper = cls.create_scraper(
            **{
                field: kwargs.pop(field, None) for field in [
                    'allow_brotli',
                    'browser',
                    'debug',
                    'delay',
                    'interpreter',
                    'recaptcha'
                ] if field in kwargs
            }
        )

        try:
            resp = scraper.get(url, **kwargs)
            resp.raise_for_status()
        except Exception:
            logging.error('"{}" returned an error. Could not collect tokens.'.format(url))
            raise

        domain = urlparse(resp.url).netloc
        # noinspection PyUnusedLocal
        cookie_domain = None

        for d in scraper.cookies.list_domains():
            if d.startswith('.') and d in ('.{}'.format(domain)):
                cookie_domain = d
                break
        else:
            sys.tracebacklimit = 0
            raise RuntimeError(
                "Unable to find Cloudflare cookies. Does the site actually "
                "have Cloudflare IUAM (I'm Under Attack Mode) enabled?"
            )

        return (
            {
                '__cfduid': scraper.cookies.get('__cfduid', '', domain=cookie_domain),
                'cf_clearance': scraper.cookies.get('cf_clearance', '', domain=cookie_domain)
            },
            scraper.headers['User-Agent']
        )

    # ------------------------------------------------------------------------------- #

    @classmethod
    def get_cookie_string(cls, url, **kwargs):
        """
        Convenience function for building a Cookie HTTP header value.
        """
        tokens, user_agent = cls.get_tokens(url, **kwargs)
        return '; '.join('='.join(pair) for pair in tokens.items()), user_agent


# ------------------------------------------------------------------------------- #

if ssl.OPENSSL_VERSION_INFO < (1, 1, 1):
    print(
        "DEPRECATION: The OpenSSL being used by this python install ({}) does not meet the minimum supported "
        "version (>= OpenSSL 1.1.1) in order to support TLS 1.3 required by Cloudflare, "
        "You may encounter an unexpected reCaptcha or cloudflare 1020 blocks.".format(
            ssl.OPENSSL_VERSION
        )
    )

# ------------------------------------------------------------------------------- #

create_scraper = CloudScraper.create_scraper
get_tokens = CloudScraper.get_tokens
get_cookie_string = CloudScraper.get_cookie_string
