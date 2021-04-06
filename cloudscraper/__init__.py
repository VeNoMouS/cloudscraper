# ------------------------------------------------------------------------------- #

import logging
import re
import requests
import sys
import ssl

from collections import OrderedDict
from copy import deepcopy

from requests.adapters import HTTPAdapter
from requests.sessions import Session
from requests_toolbelt.utils import dump

from time import sleep

# ------------------------------------------------------------------------------- #

try:
    import brotli
except ImportError:
    pass

try:
    import copyreg
except ImportError:
    import copy_reg as copyreg

try:
    from HTMLParser import HTMLParser
except ImportError:
    if sys.version_info >= (3, 4):
        import html
    else:
        from html.parser import HTMLParser

try:
    from urlparse import urlparse, urljoin
except ImportError:
    from urllib.parse import urlparse, urljoin

# ------------------------------------------------------------------------------- #

from .exceptions import (
    CloudflareLoopProtection,
    CloudflareCode1020,
    CloudflareIUAMError,
    CloudflareSolveError,
    CloudflareChallengeError,
    CloudflareCaptchaError,
    CloudflareCaptchaProvider
)

from .interpreters import JavaScriptInterpreter
from .captcha import Captcha
from .user_agent import User_Agent

# ------------------------------------------------------------------------------- #

__version__ = '1.2.58'

# ------------------------------------------------------------------------------- #


class CipherSuiteAdapter(HTTPAdapter):

    __attrs__ = [
        'ssl_context',
        'max_retries',
        'config',
        '_pool_connections',
        '_pool_maxsize',
        '_pool_block',
        'source_address'
    ]

    def __init__(self, *args, **kwargs):
        self.ssl_context = kwargs.pop('ssl_context', None)
        self.cipherSuite = kwargs.pop('cipherSuite', None)
        self.source_address = kwargs.pop('source_address', None)

        if self.source_address:
            if isinstance(self.source_address, str):
                self.source_address = (self.source_address, 0)

            if not isinstance(self.source_address, tuple):
                raise TypeError(
                    "source_address must be IP address string or (ip, port) tuple"
                )

        if not self.ssl_context:
            self.ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            self.ssl_context.set_ciphers(self.cipherSuite)
            self.ssl_context.set_ecdh_curve('prime256v1')
            self.ssl_context.options |= (ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1)

        super(CipherSuiteAdapter, self).__init__(**kwargs)

    # ------------------------------------------------------------------------------- #

    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_context'] = self.ssl_context
        kwargs['source_address'] = self.source_address
        return super(CipherSuiteAdapter, self).init_poolmanager(*args, **kwargs)

    # ------------------------------------------------------------------------------- #

    def proxy_manager_for(self, *args, **kwargs):
        kwargs['ssl_context'] = self.ssl_context
        kwargs['source_address'] = self.source_address
        return super(CipherSuiteAdapter, self).proxy_manager_for(*args, **kwargs)

# ------------------------------------------------------------------------------- #


class CloudScraper(Session):

    def __init__(self, *args, **kwargs):
        self.debug = kwargs.pop('debug', False)
        self.delay = kwargs.pop('delay', None)
        self.cipherSuite = kwargs.pop('cipherSuite', None)
        self.ssl_context = kwargs.pop('ssl_context', None)
        self.interpreter = kwargs.pop('interpreter', 'native')
        self.captcha = kwargs.pop('captcha', {})
        self.requestPreHook = kwargs.pop('requestPreHook', None)
        self.requestPostHook = kwargs.pop('requestPostHook', None)
        self.source_address = kwargs.pop('source_address', None)
        self.doubleDown = kwargs.pop('doubleDown', True)

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
            if not self.cipherSuite:
                self.cipherSuite = self.user_agent.cipherSuite

        if isinstance(self.cipherSuite, list):
            self.cipherSuite = ':'.join(self.cipherSuite)

        self.mount(
            'https://',
            CipherSuiteAdapter(
                cipherSuite=self.cipherSuite,
                ssl_context=self.ssl_context,
                source_address=self.source_address
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
    # Allow replacing actual web request call via subclassing
    # ------------------------------------------------------------------------------- #

    def perform_request(self, method, url, *args, **kwargs):
        return super(CloudScraper, self).request(method, url, *args, **kwargs)

    # ------------------------------------------------------------------------------- #
    # Raise an Exception with no stacktrace and reset depth counter.
    # ------------------------------------------------------------------------------- #

    def simpleException(self, exception, msg):
        self._solveDepthCnt = 0
        sys.tracebacklimit = 0
        raise exception(msg)

    # ------------------------------------------------------------------------------- #
    # debug the request via the response
    # ------------------------------------------------------------------------------- #

    @staticmethod
    def debugRequest(req):
        try:
            print(dump.dump_all(req).decode('utf-8', errors='backslashreplace'))
        except ValueError as e:
            print(f"Debug Error: {getattr(e, 'message', e)}")

    # ------------------------------------------------------------------------------- #
    # Unescape / decode html entities
    # ------------------------------------------------------------------------------- #

    @staticmethod
    def unescape(html_text):
        if sys.version_info >= (3, 0):
            if sys.version_info >= (3, 4):
                return html.unescape(html_text)

            return HTMLParser().unescape(html_text)

        return HTMLParser().unescape(html_text)

    # ------------------------------------------------------------------------------- #
    # Decode Brotli on older versions of urllib3 manually
    # ------------------------------------------------------------------------------- #

    def decodeBrotli(self, resp):
        if requests.packages.urllib3.__version__ < '1.25.1' and resp.headers.get('Content-Encoding') == 'br':
            if self.allow_brotli and resp._content:
                resp._content = brotli.decompress(resp.content)
            else:
                logging.warning(
                    f'You\'re running urllib3 {requests.packages.urllib3.__version__}, Brotli content detected, '
                    'Which requires manual decompression, '
                    'But option allow_brotli is set to False, '
                    'We will not continue to decompress.'
                )

        return resp

    # ------------------------------------------------------------------------------- #
    # Our hijacker request function
    # ------------------------------------------------------------------------------- #

    def request(self, method, url, *args, **kwargs):
        # pylint: disable=E0203
        if kwargs.get('proxies') and kwargs.get('proxies') != self.proxies:
            self.proxies = kwargs.get('proxies')

        # ------------------------------------------------------------------------------- #
        # Pre-Hook the request via user defined function.
        # ------------------------------------------------------------------------------- #

        if self.requestPreHook:
            (method, url, args, kwargs) = self.requestPreHook(
                self,
                method,
                url,
                *args,
                **kwargs
            )

        # ------------------------------------------------------------------------------- #
        # Make the request via requests.
        # ------------------------------------------------------------------------------- #

        response = self.decodeBrotli(
            self.perform_request(method, url, *args, **kwargs)
        )

        # ------------------------------------------------------------------------------- #
        # Debug the request via the Response object.
        # ------------------------------------------------------------------------------- #

        if self.debug:
            self.debugRequest(response)

        # ------------------------------------------------------------------------------- #
        # Post-Hook the request aka Post-Hook the response via user defined function.
        # ------------------------------------------------------------------------------- #

        if self.requestPostHook:
            response = self.requestPostHook(self, response)

            if self.debug:
                self.debugRequest(response)

        # Check if Cloudflare anti-bot is on
        if self.is_Challenge_Request(response):
            # ------------------------------------------------------------------------------- #
            # Try to solve the challenge and send it back
            # ------------------------------------------------------------------------------- #

            if self._solveDepthCnt >= self.solveDepth:
                _ = self._solveDepthCnt
                self.simpleException(
                    CloudflareLoopProtection,
                    f"!!Loop Protection!! We have tried to solve {_} time(s) in a row."
                )

            self._solveDepthCnt += 1

            response = self.Challenge_Response(response, **kwargs)
        else:
            if not response.is_redirect and response.status_code not in [429, 503]:
                self._solveDepthCnt = 0

        return response

    # ------------------------------------------------------------------------------- #
    # check if the response contains a valid Cloudflare Bot Fight Mode challenge
    # ------------------------------------------------------------------------------- #

    @staticmethod
    def is_BFM_Challenge(resp):
        try:
            return (
                resp.headers.get('Server', '').startswith('cloudflare')
                and re.search(
                    r"\/cdn-cgi\/bm\/cv\/\d+\/api\.js.*?"
                    r"window\['__CF\$cv\$params'\]\s*=\s*{",
                    resp.text,
                    re.M | re.S
                )
            )
        except AttributeError:
            pass

        return False

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
                    r'<form .*?="challenge-form" action="/.*?__cf_chl_jschl_tk__=\S+"',
                    resp.text,
                    re.M | re.S
                )
            )
        except AttributeError:
            pass

        return False

    # ------------------------------------------------------------------------------- #
    # check if the response contains new Cloudflare challenge
    # ------------------------------------------------------------------------------- #

    @staticmethod
    def is_New_IUAM_Challenge(resp):
        try:
            return (
                resp.headers.get('Server', '').startswith('cloudflare')
                and resp.status_code in [429, 503]
                and re.search(
                    r'cpo.src\s*=\s*"/cdn-cgi/challenge-platform/\S+orchestrate/jsch/v1',
                    resp.text,
                    re.M | re.S
                )
                and re.search(r'window._cf_chl_enter\s*[\(=]', resp.text, re.M | re.S)
            )
        except AttributeError:
            pass

        return False

    # ------------------------------------------------------------------------------- #
    # check if the response contains a v2 hCaptcha Cloudflare challenge
    # ------------------------------------------------------------------------------- #

    @staticmethod
    def is_New_Captcha_Challenge(resp):
        try:
            return (
                CloudScraper.is_Captcha_Challenge(resp)
                and re.search(
                    r'cpo.src\s*=\s*"/cdn-cgi/challenge-platform/\S+orchestrate/captcha/v1',
                    resp.text,
                    re.M | re.S
                )
                and re.search(r'\s*id="trk_captcha_js"', resp.text, re.M | re.S)
            )
        except AttributeError:
            pass

        return False

    # ------------------------------------------------------------------------------- #
    # check if the response contains a Cloudflare hCaptcha challenge
    # ------------------------------------------------------------------------------- #

    @staticmethod
    def is_Captcha_Challenge(resp):
        try:
            return (
                resp.headers.get('Server', '').startswith('cloudflare')
                and resp.status_code == 403
                and re.search(
                    r'action="/\S+__cf_chl_captcha_tk__=\S+',
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
    # Wrapper for is_Captcha_Challenge, is_IUAM_Challenge, is_Firewall_Blocked
    # ------------------------------------------------------------------------------- #

    def is_Challenge_Request(self, resp):
        if self.is_Firewall_Blocked(resp):
            self.simpleException(
                CloudflareCode1020,
                'Cloudflare has blocked this request (Code 1020 Detected).'
            )

        if self.is_New_Captcha_Challenge(resp):
            self.simpleException(
                CloudflareChallengeError,
                'Detected a Cloudflare version 2 Captcha challenge, This feature is not available in the opensource (free) version.'
            )

        if self.is_New_IUAM_Challenge(resp):
            self.simpleException(
                CloudflareChallengeError,
                'Detected a Cloudflare version 2 challenge, This feature is not available in the opensource (free) version.'
            )

        if self.is_Captcha_Challenge(resp) or self.is_IUAM_Challenge(resp):
            if self.debug:
                print('Detected a Cloudflare version 1 challenge.')
            return True

        return False

    # ------------------------------------------------------------------------------- #
    # Try to solve cloudflare javascript challenge.
    # ------------------------------------------------------------------------------- #

    def IUAM_Challenge_Response(self, body, url, interpreter):
        try:
            formPayload = re.search(
                r'<form (?P<form>.*?="challenge-form" '
                r'action="(?P<challengeUUID>.*?'
                r'__cf_chl_jschl_tk__=\S+)"(.*?)</form>)',
                body,
                re.M | re.DOTALL
            ).groupdict()

            if not all(key in formPayload for key in ['form', 'challengeUUID']):
                self.simpleException(
                    CloudflareIUAMError,
                    "Cloudflare IUAM detected, unfortunately we can't extract the parameters correctly."
                )

            payload = OrderedDict()
            for challengeParam in re.findall(r'^\s*<input\s(.*?)/>', formPayload['form'], re.M | re.S):
                inputPayload = dict(re.findall(r'(\S+)="(\S+)"', challengeParam))
                if inputPayload.get('name') in ['r', 'jschl_vc', 'pass']:
                    payload.update({inputPayload['name']: inputPayload['value']})

        except AttributeError:
            self.simpleException(
                CloudflareIUAMError,
                "Cloudflare IUAM detected, unfortunately we can't extract the parameters correctly."
            )

        hostParsed = urlparse(url)

        try:
            payload['jschl_answer'] = JavaScriptInterpreter.dynamicImport(
                interpreter
            ).solveChallenge(body, hostParsed.netloc)
        except Exception as e:
            self.simpleException(
                CloudflareIUAMError,
                f"Unable to parse Cloudflare anti-bots page: {getattr(e, 'message', e)}"
            )

        return {
            'url': f"{hostParsed.scheme}://{hostParsed.netloc}{self.unescape(formPayload['challengeUUID'])}",
            'data': payload
        }

    # ------------------------------------------------------------------------------- #
    #  Try to solve the Captcha challenge via 3rd party.
    # ------------------------------------------------------------------------------- #

    def captcha_Challenge_Response(self, provider, provider_params, body, url):
        try:
            formPayload = re.search(
                r'<form (?P<form>.*?="challenge-form" '
                r'action="(?P<challengeUUID>.*?__cf_chl_captcha_tk__=\S+)"(.*?)</form>)',
                body,
                re.M | re.DOTALL
            ).groupdict()

            if not all(key in formPayload for key in ['form', 'challengeUUID']):
                self.simpleException(
                    CloudflareCaptchaError,
                    "Cloudflare Captcha detected, unfortunately we can't extract the parameters correctly."
                )

            payload = OrderedDict(
                re.findall(
                    r'(name="r"\svalue|data-ray|data-sitekey|name="cf_captcha_kind"\svalue)="(.*?)"',
                    formPayload['form']
                )
            )

            captchaType = 'reCaptcha' if payload['name="cf_captcha_kind" value'] == 're' else 'hCaptcha'

        except (AttributeError, KeyError):
            self.simpleException(
                CloudflareCaptchaError,
                "Cloudflare Captcha detected, unfortunately we can't extract the parameters correctly."
            )

        # ------------------------------------------------------------------------------- #
        # Pass proxy parameter to provider to solve captcha.
        # ------------------------------------------------------------------------------- #

        if self.proxies and self.proxies != self.captcha.get('proxy'):
            self.captcha['proxy'] = self.proxies

        # ------------------------------------------------------------------------------- #
        # Pass User-Agent if provider supports it to solve captcha.
        # ------------------------------------------------------------------------------- #

        self.captcha['User-Agent'] = self.headers['User-Agent']

        # ------------------------------------------------------------------------------- #
        # Submit job to provider to request captcha solve.
        # ------------------------------------------------------------------------------- #

        captchaResponse = Captcha.dynamicImport(
            provider.lower()
        ).solveCaptcha(
            captchaType,
            url,
            payload['data-sitekey'],
            provider_params
        )

        # ------------------------------------------------------------------------------- #
        # Parse and handle the response of solved captcha.
        # ------------------------------------------------------------------------------- #

        dataPayload = OrderedDict([
            ('r', payload.get('name="r" value', '')),
            ('cf_captcha_kind', payload['name="cf_captcha_kind" value']),
            ('id', payload.get('data-ray')),
            ('g-recaptcha-response', captchaResponse)
        ])

        if captchaType == 'hCaptcha':
            dataPayload.update({'h-captcha-response': captchaResponse})

        hostParsed = urlparse(url)

        return {
            'url': f"{hostParsed.scheme}://{hostParsed.netloc}{self.unescape(formPayload['challengeUUID'])}",
            'data': dataPayload
        }

    # ------------------------------------------------------------------------------- #
    # Attempt to handle and send the challenge response back to cloudflare
    # ------------------------------------------------------------------------------- #

    def Challenge_Response(self, resp, **kwargs):
        if self.is_Captcha_Challenge(resp):
            # ------------------------------------------------------------------------------- #
            # double down on the request as some websites are only checking
            # if cfuid is populated before issuing Captcha.
            # ------------------------------------------------------------------------------- #

            if self.doubleDown:
                resp = self.decodeBrotli(
                    self.perform_request(resp.request.method, resp.url, **kwargs)
                )

            if not self.is_Captcha_Challenge(resp):
                return resp

            # ------------------------------------------------------------------------------- #
            # if no captcha provider raise a runtime error.
            # ------------------------------------------------------------------------------- #

            if not self.captcha or not isinstance(self.captcha, dict) or not self.captcha.get('provider'):
                self.simpleException(
                    CloudflareCaptchaProvider,
                    "Cloudflare Captcha detected, unfortunately you haven't loaded an anti Captcha provider "
                    "correctly via the 'captcha' parameter."
                )

            # ------------------------------------------------------------------------------- #
            # if provider is return_response, return the response without doing anything.
            # ------------------------------------------------------------------------------- #

            if self.captcha.get('provider') == 'return_response':
                return resp

            # ------------------------------------------------------------------------------- #
            # Submit request to parser wrapper to solve captcha
            # ------------------------------------------------------------------------------- #

            submit_url = self.captcha_Challenge_Response(
                self.captcha.get('provider'),
                self.captcha,
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
                    self.simpleException(
                        CloudflareIUAMError,
                        "Cloudflare IUAM possibility malformed, issue extracing delay value."
                    )

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
                    'Origin': f'{urlParsed.scheme}://{urlParsed.netloc}',
                    'Referer': resp.url
                }
            )

            challengeSubmitResponse = self.request(
                'POST',
                submit_url['url'],
                **cloudflare_kwargs
            )

            if challengeSubmitResponse.status_code == 400:
                self.simpleException(
                    CloudflareSolveError,
                    'Invalid challenge answer detected, Cloudflare broken?'
                )

            # ------------------------------------------------------------------------------- #
            # Return response if Cloudflare is doing content pass through instead of 3xx
            # else request with redirect URL also handle protocol scheme change http -> https
            # ------------------------------------------------------------------------------- #

            if not challengeSubmitResponse.is_redirect:
                return challengeSubmitResponse

            else:
                cloudflare_kwargs = deepcopy(kwargs)
                cloudflare_kwargs['headers'] = updateAttr(
                    cloudflare_kwargs,
                    'headers',
                    {'Referer': challengeSubmitResponse.url}
                )

                if not urlparse(challengeSubmitResponse.headers['Location']).netloc:
                    redirect_location = urljoin(
                        challengeSubmitResponse.url,
                        challengeSubmitResponse.headers['Location']
                    )
                else:
                    redirect_location = challengeSubmitResponse.headers['Location']

                return self.request(
                    resp.request.method,
                    redirect_location,
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
                    'doubleDown',
                    'captcha',
                    'interpreter',
                    'source_address'
                    'requestPreHook',
                    'requestPostHook'
                ] if field in kwargs
            }
        )

        try:
            resp = scraper.get(url, **kwargs)
            resp.raise_for_status()
        except Exception:
            logging.error(f'"{url}" returned an error. Could not collect tokens.')
            raise

        domain = urlparse(resp.url).netloc
        # noinspection PyUnusedLocal
        cookie_domain = None

        for d in scraper.cookies.list_domains():
            if d.startswith('.') and d in (f'.{domain}'):
                cookie_domain = d
                break
        else:
            cls.simpleException(
                CloudflareIUAMError,
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
        f"DEPRECATION: The OpenSSL being used by this python install ({ssl.OPENSSL_VERSION}) does not meet the minimum supported "
        "version (>= OpenSSL 1.1.1) in order to support TLS 1.3 required by Cloudflare, "
        "You may encounter an unexpected Captcha or cloudflare 1020 blocks."
    )

# ------------------------------------------------------------------------------- #

create_scraper = CloudScraper.create_scraper
get_tokens = CloudScraper.get_tokens
get_cookie_string = CloudScraper.get_cookie_string
