import logging
import re
import sys
import ssl

from copy import deepcopy
from time import sleep
from collections import OrderedDict

from requests.sessions import Session
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.ssl_ import create_urllib3_context

from .interpreters import JavaScriptInterpreter
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
    from urlparse import urlunparse
except ImportError:
    from urllib.parse import urlparse
    from urllib.parse import urlunparse

##########################################################################################################################################################

__version__ = '1.1.9'

BUG_REPORT = 'Cloudflare may have changed their technique, or there may be a bug in the script.'

##########################################################################################################################################################


class CipherSuiteAdapter(HTTPAdapter):

    def __init__(self, cipherSuite=None, **kwargs):
        self.cipherSuite = cipherSuite

        if hasattr(ssl, 'PROTOCOL_TLS'):
            self.ssl_context = create_urllib3_context(
                ssl_version=getattr(ssl, 'PROTOCOL_TLSv1_3', ssl.PROTOCOL_TLSv1_2),
                ciphers=self.cipherSuite
            )
        else:
            self.ssl_context = create_urllib3_context(ssl_version=ssl.PROTOCOL_TLSv1)

        super(CipherSuiteAdapter, self).__init__(**kwargs)

    ##########################################################################################################################################################

    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_context'] = self.ssl_context
        return super(CipherSuiteAdapter, self).init_poolmanager(*args, **kwargs)

    ##########################################################################################################################################################

    def proxy_manager_for(self, *args, **kwargs):
        kwargs['ssl_context'] = self.ssl_context
        return super(CipherSuiteAdapter, self).proxy_manager_for(*args, **kwargs)

##########################################################################################################################################################


class CloudScraper(Session):
    def __init__(self, *args, **kwargs):
        self.debug = kwargs.pop('debug', False)
        self.delay = kwargs.pop('delay', None)
        self.interpreter = kwargs.pop('interpreter', 'js2py')
        self.allow_brotli = kwargs.pop('allow_brotli', True if 'brotli' in sys.modules.keys() else False)
        self.cipherSuite = None

        super(CloudScraper, self).__init__(*args, **kwargs)

        if 'requests' in self.headers['User-Agent']:
            # Set a random User-Agent if no custom User-Agent has been set
            self.headers = User_Agent(allow_brotli=self.allow_brotli).headers

        self.mount('https://', CipherSuiteAdapter(self.loadCipherSuite()))

    ##########################################################################################################################################################

    @staticmethod
    def debugRequest(req):
        try:
            print(dump.dump_all(req).decode('utf-8'))
        except:  # noqa
            pass

    ##########################################################################################################################################################

    def loadCipherSuite(self):
        if self.cipherSuite:
            return self.cipherSuite

        self.cipherSuite = ''

        if hasattr(ssl, 'PROTOCOL_TLS'):
            ciphers = [
                'ECDHE-ECDSA-AES128-GCM-SHA256', 'ECDHE-RSA-AES128-GCM-SHA256', 'ECDHE-ECDSA-AES256-GCM-SHA384',
                'ECDHE-RSA-AES256-GCM-SHA384', 'ECDHE-ECDSA-CHACHA20-POLY1305-SHA256', 'ECDHE-RSA-CHACHA20-POLY1305-SHA256',
                'ECDHE-RSA-AES128-CBC-SHA', 'ECDHE-RSA-AES256-CBC-SHA', 'RSA-AES128-GCM-SHA256', 'RSA-AES256-GCM-SHA384',
                'ECDHE-RSA-AES128-GCM-SHA256', 'RSA-AES256-SHA', '3DES-EDE-CBC'
            ]

            if hasattr(ssl, 'PROTOCOL_TLSv1_3'):
                ciphers.insert(0, ['GREASE_3A', 'GREASE_6A', 'AES128-GCM-SHA256', 'AES256-GCM-SHA256', 'AES256-GCM-SHA384', 'CHACHA20-POLY1305-SHA256'])

            ctx = ssl.SSLContext(getattr(ssl, 'PROTOCOL_TLSv1_3', ssl.PROTOCOL_TLSv1_2))

            for cipher in ciphers:
                try:
                    ctx.set_ciphers(cipher)
                    self.cipherSuite = '{}:{}'.format(self.cipherSuite, cipher).rstrip(':')
                except ssl.SSLError:
                    pass

        return self.cipherSuite

    ##########################################################################################################################################################

    def request(self, method, url, *args, **kwargs):
        ourSuper = super(CloudScraper, self)
        resp = ourSuper.request(method, url, *args, **kwargs)

        if resp.headers.get('Content-Encoding') == 'br':
            if self.allow_brotli and resp._content:
                resp._content = brotli.decompress(resp.content)
            else:
                logging.warning('Brotli content detected, But option is disabled, we will not continue.')
                return resp

        # Debug request
        if self.debug:
            self.debugRequest(resp)

        # Check if Cloudflare anti-bot is on
        if self.isChallengeRequest(resp):
            if resp.request.method != 'GET':
                # Work around if the initial request is not a GET,
                # Supersede with a GET then re-request the original METHOD.
                self.request('GET', resp.url)
                resp = ourSuper.request(method, url, *args, **kwargs)
            else:
                # Solve Challenge
                resp = self.sendChallengeResponse(resp, **kwargs)

        return resp

    ##########################################################################################################################################################

    @staticmethod
    def isChallengeRequest(resp):
        if resp.headers.get('Server', '').startswith('cloudflare'):
            if b'why_captcha' in resp.content or b'/cdn-cgi/l/chk_captcha' in resp.content:
                raise ValueError('Captcha')

            return (
                resp.status_code in [429, 503]
                and all(s in resp.content for s in [b'jschl_vc', b'jschl_answer'])
            )

        return False

    ##########################################################################################################################################################

    def sendChallengeResponse(self, resp, **original_kwargs):
        body = resp.text

        # Cloudflare requires a delay before solving the challenge
        if not self.delay:
            try:
                delay = float(re.search(r'submit\(\);\r?\n\s*},\s*([0-9]+)', body).group(1)) / float(1000)
                if isinstance(delay, (int, float)):
                    self.delay = delay
            except:  # noqa
                pass

        sleep(self.delay)

        parsed_url = urlparse(resp.url)
        domain = parsed_url.netloc
        submit_url = '{}://{}/cdn-cgi/l/chk_jschl'.format(parsed_url.scheme, domain)

        cloudflare_kwargs = deepcopy(original_kwargs)

        try:
            params = OrderedDict()

            s = re.search(r'name="s"\svalue="(?P<s_value>[^"]+)', body)
            if s:
                params['s'] = s.group('s_value')

            params.update(
                [
                    ('jschl_vc', re.search(r'name="jschl_vc" value="(\w+)"', body).group(1)),
                    ('pass', re.search(r'name="pass" value="(.+?)"', body).group(1))
                ]
            )

            params = cloudflare_kwargs.setdefault('params', params)

        except Exception as e:
            raise ValueError('Unable to parse Cloudflare anti-bots page: {} {}'.format(e.message, BUG_REPORT))

        # Solve the Javascript challenge
        params['jschl_answer'] = JavaScriptInterpreter.dynamicImport(self.interpreter).solveChallenge(body, domain)

        # Requests transforms any request into a GET after a redirect,
        # so the redirect has to be handled manually here to allow for
        # performing other types of requests even as the first request.

        cloudflare_kwargs['allow_redirects'] = False

        redirect = self.request(resp.request.method, submit_url, **cloudflare_kwargs)
        redirect_location = urlparse(redirect.headers['Location'])
        if not redirect_location.netloc:
            redirect_url = urlunparse(
                (
                    parsed_url.scheme,
                    domain,
                    redirect_location.path,
                    redirect_location.params,
                    redirect_location.query,
                    redirect_location.fragment
                )
            )
            return self.request(resp.request.method, redirect_url, **original_kwargs)

        return self.request(resp.request.method, redirect.headers['Location'], **original_kwargs)

    ##########################################################################################################################################################

    @classmethod
    def create_scraper(cls, sess=None, **kwargs):
        """
        Convenience function for creating a ready-to-go CloudScraper object.
        """
        scraper = cls(**kwargs)

        if sess:
            attrs = ['auth', 'cert', 'cookies', 'headers', 'hooks', 'params', 'proxies', 'data']
            for attr in attrs:
                val = getattr(sess, attr, None)
                if val:
                    setattr(scraper, attr, val)

        return scraper

    ##########################################################################################################################################################

    # Functions for integrating cloudscraper with other applications and scripts
    @classmethod
    def get_tokens(cls, url, **kwargs):
        scraper = cls.create_scraper(
            debug=kwargs.pop('debug', False),
            delay=kwargs.pop('delay', None),
            interpreter=kwargs.pop('interpreter', 'js2py'),
            allow_brotli=kwargs.pop('allow_brotli', True),
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
            raise ValueError('Unable to find Cloudflare cookies. Does the site actually have Cloudflare IUAM ("I\'m Under Attack Mode") enabled?')

        return (
            {
                '__cfduid': scraper.cookies.get('__cfduid', '', domain=cookie_domain),
                'cf_clearance': scraper.cookies.get('cf_clearance', '', domain=cookie_domain)
            },
            scraper.headers['User-Agent']
        )

    ##########################################################################################################################################################

    @classmethod
    def get_cookie_string(cls, url, **kwargs):
        """
        Convenience function for building a Cookie HTTP header value.
        """
        tokens, user_agent = cls.get_tokens(url, **kwargs)
        return '; '.join('='.join(pair) for pair in tokens.items()), user_agent


##########################################################################################################################################################

create_scraper = CloudScraper.create_scraper
get_tokens = CloudScraper.get_tokens
get_cookie_string = CloudScraper.get_cookie_string
