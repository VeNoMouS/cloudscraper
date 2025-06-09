# ------------------------------------------------------------------------------- #

import logging
import requests
import sys
import ssl
import time
from typing import Optional, Dict, Any, Union, List

from requests.adapters import HTTPAdapter
from requests.sessions import Session
from requests_toolbelt.utils import dump

# ------------------------------------------------------------------------------- #

try:
    import brotli
except ImportError:
    pass

import copyreg
from urllib.parse import urlparse

# ------------------------------------------------------------------------------- #

from .exceptions import (
    CloudflareLoopProtection,
    CloudflareIUAMError,
    CloudflareChallengeError,
    CloudflareTurnstileError,
    CloudflareV3Error
)

from .cloudflare import Cloudflare
from .cloudflare_v2 import CloudflareV2
from .cloudflare_v3 import CloudflareV3
from .turnstile import CloudflareTurnstile
from .user_agent import User_Agent
from .proxy_manager import ProxyManager
from .stealth import StealthMode

# ------------------------------------------------------------------------------- #

__version__ = '3.0.0'

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
        self.server_hostname = kwargs.pop('server_hostname', None)
        self.ecdhCurve = kwargs.pop('ecdhCurve', 'prime256v1')

        if self.source_address:
            if isinstance(self.source_address, str):
                self.source_address = (self.source_address, 0)

            if not isinstance(self.source_address, tuple):
                raise TypeError(
                    "source_address must be IP address string or (ip, port) tuple"
                )

        if not self.ssl_context:
            self.ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)

            self.ssl_context.orig_wrap_socket = self.ssl_context.wrap_socket
            self.ssl_context.wrap_socket = self.wrap_socket

            if self.server_hostname:
                self.ssl_context.server_hostname = self.server_hostname

            self.ssl_context.set_ciphers(self.cipherSuite)
            self.ssl_context.set_ecdh_curve(self.ecdhCurve)

            self.ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            self.ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3

        super(CipherSuiteAdapter, self).__init__(**kwargs)

    # ------------------------------------------------------------------------------- #

    def wrap_socket(self, *args, **kwargs):
        if hasattr(self.ssl_context, 'server_hostname') and self.ssl_context.server_hostname:
            kwargs['server_hostname'] = self.ssl_context.server_hostname
            self.ssl_context.check_hostname = False
        else:
            self.ssl_context.check_hostname = True

        return self.ssl_context.orig_wrap_socket(*args, **kwargs)

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

        # Cloudflare challenge handling options
        self.disableCloudflareV1 = kwargs.pop('disableCloudflareV1', False)
        self.disableCloudflareV2 = kwargs.pop('disableCloudflareV2', False)
        self.disableCloudflareV3 = kwargs.pop('disableCloudflareV3', False)
        self.disableTurnstile = kwargs.pop('disableTurnstile', False)
        self.delay = kwargs.pop('delay', None)
        self.captcha = kwargs.pop('captcha', {})
        self.doubleDown = kwargs.pop('doubleDown', True)
        self.interpreter = kwargs.pop('interpreter', 'js2py')  # Default to js2py for better compatibility

        # Request hooks
        self.requestPreHook = kwargs.pop('requestPreHook', None)
        self.requestPostHook = kwargs.pop('requestPostHook', None)

        # TLS/SSL options
        self.cipherSuite = kwargs.pop('cipherSuite', None)
        self.ecdhCurve = kwargs.pop('ecdhCurve', 'prime256v1')
        self.source_address = kwargs.pop('source_address', None)
        self.server_hostname = kwargs.pop('server_hostname', None)
        self.ssl_context = kwargs.pop('ssl_context', None)

        # Compression options
        self.allow_brotli = kwargs.pop(
            'allow_brotli',
            True if 'brotli' in sys.modules.keys() else False
        )

        # User agent handling
        self.user_agent = User_Agent(
            allow_brotli=self.allow_brotli,
            browser=kwargs.pop('browser', None)
        )

        # Challenge solving depth
        self._solveDepthCnt = 0
        self.solveDepth = kwargs.pop('solveDepth', 3)

        # Session health monitoring
        self.session_start_time = time.time()
        self.request_count = 0
        self.last_403_time = 0
        self.session_refresh_interval = kwargs.pop('session_refresh_interval', 3600)  # 1 hour default
        self.auto_refresh_on_403 = kwargs.pop('auto_refresh_on_403', True)
        self.max_403_retries = kwargs.pop('max_403_retries', 3)
        self._403_retry_count = 0

        # Request throttling and TLS management
        self.last_request_time = 0
        self.min_request_interval = kwargs.pop('min_request_interval', 1.0)  # Minimum 1 second between requests
        self.max_concurrent_requests = kwargs.pop('max_concurrent_requests', 1)  # Limit concurrent requests
        self.current_concurrent_requests = 0
        self.rotate_tls_ciphers = kwargs.pop('rotate_tls_ciphers', True)  # Enable TLS cipher rotation
        self._cipher_rotation_count = 0

        # Proxy management
        proxy_options = kwargs.pop('proxy_options', {})
        self.proxy_manager = ProxyManager(
            proxies=kwargs.pop('rotating_proxies', None),
            proxy_rotation_strategy=proxy_options.get('rotation_strategy', 'sequential'),
            ban_time=proxy_options.get('ban_time', 300)
        )

        # Stealth mode
        self.stealth_mode = StealthMode(self)
        self.enable_stealth = kwargs.pop('enable_stealth', True)

        # Stealth mode configuration
        stealth_options = kwargs.pop('stealth_options', {})
        if stealth_options:
            if 'min_delay' in stealth_options and 'max_delay' in stealth_options:
                self.stealth_mode.set_delay_range(
                    stealth_options['min_delay'],
                    stealth_options['max_delay']
                )
            self.stealth_mode.enable_human_like_delays(stealth_options.get('human_like_delays', True))
            self.stealth_mode.enable_randomize_headers(stealth_options.get('randomize_headers', True))
            self.stealth_mode.enable_browser_quirks(stealth_options.get('browser_quirks', True))

        # Initialize the session
        super(CloudScraper, self).__init__(*args, **kwargs)

        # Set up User-Agent and headers
        if 'requests' in self.headers.get('User-Agent', ''):
            # Set a random User-Agent if no custom User-Agent has been set
            self.headers = self.user_agent.headers
            if not self.cipherSuite:
                self.cipherSuite = self.user_agent.cipherSuite

        if isinstance(self.cipherSuite, list):
            self.cipherSuite = ':'.join(self.cipherSuite)

        # Mount the HTTPS adapter with our custom cipher suite
        self.mount(
            'https://',
            CipherSuiteAdapter(
                cipherSuite=self.cipherSuite,
                ecdhCurve=self.ecdhCurve,
                server_hostname=self.server_hostname,
                source_address=self.source_address,
                ssl_context=self.ssl_context
            )
        )

        # Initialize Cloudflare handlers
        self.cloudflare_v1 = Cloudflare(self)
        self.cloudflare_v2 = CloudflareV2(self)
        self.cloudflare_v3 = CloudflareV3(self)
        self.turnstile = CloudflareTurnstile(self)

        # Allow pickle serialization
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
        # Apply request throttling to prevent TLS blocking
        self._apply_request_throttling()

        # Rotate TLS cipher suites to avoid detection
        if self.rotate_tls_ciphers:
            self._rotate_tls_cipher_suite()

        # Check if session needs refresh due to age
        if self._should_refresh_session():
            self._refresh_session(url)

        # Handle proxy rotation if no specific proxies are provided
        if not kwargs.get('proxies') and hasattr(self, 'proxy_manager') and self.proxy_manager.proxies:
            kwargs['proxies'] = self.proxy_manager.get_proxy()
        elif kwargs.get('proxies') and kwargs.get('proxies') != self.proxies:
            self.proxies = kwargs.get('proxies')

        # Apply stealth techniques if enabled
        if self.enable_stealth:
            kwargs = self.stealth_mode.apply_stealth_techniques(method, url, **kwargs)

        # Track request count
        self.request_count += 1

        # Track concurrent requests
        self.current_concurrent_requests += 1

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

        try:
            response = self.decodeBrotli(
                self.perform_request(method, url, *args, **kwargs)
            )

            # Report successful proxy use if applicable
            if kwargs.get('proxies') and hasattr(self, 'proxy_manager'):
                self.proxy_manager.report_success(kwargs['proxies'])

        except (requests.exceptions.ProxyError, requests.exceptions.ConnectionError) as e:
            # Report failed proxy use if applicable
            if kwargs.get('proxies') and hasattr(self, 'proxy_manager'):
                self.proxy_manager.report_failure(kwargs['proxies'])

            # CRITICAL FIX: Always decrement concurrent request counter on exception
            if self.current_concurrent_requests > 0:
                self.current_concurrent_requests -= 1
            raise e
        except Exception as e:
            # CRITICAL FIX: Always decrement concurrent request counter on any exception
            if self.current_concurrent_requests > 0:
                self.current_concurrent_requests -= 1
            raise e

        # ------------------------------------------------------------------------------- #
        # Debug the request via the Response object.
        # ------------------------------------------------------------------------------- #

        if self.debug:
            self.debugRequest(response)

        # ------------------------------------------------------------------------------- #
        # Post-Hook the request aka Post-Hook the response via user defined function.
        # ------------------------------------------------------------------------------- #

        if self.requestPostHook:
            newResponse = self.requestPostHook(self, response)

            if response != newResponse:
                response = newResponse
                if self.debug:
                    print('==== requestPostHook Debug ====')
                    self.debugRequest(response)

        # ------------------------------------------------------------------------------- #
        # Handle Cloudflare challenges
        # ------------------------------------------------------------------------------- #

        # Check for loop protection
        if self._solveDepthCnt >= self.solveDepth:
            _ = self._solveDepthCnt
            self.simpleException(
                CloudflareLoopProtection,
                f"!!Loop Protection!! We have tried to solve {_} time(s) in a row."
            )

        # Check for Cloudflare Turnstile challenges first (if not disabled)
        if not self.disableTurnstile:
            # Check for Turnstile Challenge
            if self.turnstile.is_Turnstile_Challenge(response):
                if self.debug:
                    print('Detected a Cloudflare Turnstile challenge.')
                self._solveDepthCnt += 1
                response = self.turnstile.handle_Turnstile_Challenge(response, **kwargs)
                return response

        # Check for Cloudflare v3 challenges (if not disabled)
        if not self.disableCloudflareV3:
            # Check for v3 JavaScript VM Challenge
            if self.cloudflare_v3.is_V3_Challenge(response):
                if self.debug:
                    print('Detected a Cloudflare v3 JavaScript VM challenge.')
                self._solveDepthCnt += 1
                response = self.cloudflare_v3.handle_V3_Challenge(response, **kwargs)
                return response

        # Check for Cloudflare v2 challenges (if not disabled)
        if not self.disableCloudflareV2:
            # Check for v2 Captcha Challenge
            if self.cloudflare_v2.is_V2_Captcha_Challenge(response):
                self._solveDepthCnt += 1
                response = self.cloudflare_v2.handle_V2_Captcha_Challenge(response, **kwargs)
                return response

            # Check for v2 JavaScript Challenge
            if self.cloudflare_v2.is_V2_Challenge(response):
                self._solveDepthCnt += 1
                response = self.cloudflare_v2.handle_V2_Challenge(response, **kwargs)
                return response

        # Check for Cloudflare v1 challenges (if not disabled)
        if not self.disableCloudflareV1:
            # Check if Cloudflare v1 anti-bot is on
            if self.cloudflare_v1.is_Challenge_Request(response):
                # Try to solve the challenge and send it back
                self._solveDepthCnt += 1
                response = self.cloudflare_v1.Challenge_Response(response, **kwargs)
                return response

        # Reset solve depth counter if no challenge was detected
        if not response.is_redirect and response.status_code not in [429, 503]:
            self._solveDepthCnt = 0
            # Reset 403 retry count on successful request (ONLY if not in retry mode)
            if response.status_code == 200 and not hasattr(self, '_in_403_retry'):
                self._403_retry_count = 0

        # Handle 403 errors with automatic session refresh
        if response.status_code == 403 and self.auto_refresh_on_403:
            if self._403_retry_count < self.max_403_retries:
                self._403_retry_count += 1
                self.last_403_time = time.time()

                if self.debug:
                    print(f'🛡️ Received 403 error, attempting session refresh (attempt {self._403_retry_count}/{self.max_403_retries})')

                # Try to refresh the session and retry the request
                if self._refresh_session(url):
                    if self.debug:
                        print(f'🔄 Session refreshed successfully, retrying original request...')

                    # Mark that we're in a retry to prevent retry count reset
                    self._in_403_retry = True
                    try:
                        # Retry the original request
                        retry_response = self.request(method, url, *args, **kwargs)

                        # If retry was successful, reset retry count and return
                        if retry_response.status_code == 200:
                            self._403_retry_count = 0
                            if self.debug:
                                print('✅ 403 retry successful, request completed')

                        return retry_response
                    finally:
                        # Always clear the retry flag
                        if hasattr(self, '_in_403_retry'):
                            delattr(self, '_in_403_retry')
                else:
                    if self.debug:
                        print('❌ Session refresh failed, returning 403 response')
            else:
                if self.debug:
                    print(f'❌ Max 403 retries ({self.max_403_retries}) exceeded, returning 403 response')

        # Decrement concurrent request counter
        if self.current_concurrent_requests > 0:
            self.current_concurrent_requests -= 1

        return response

    # ------------------------------------------------------------------------------- #
    # Session health monitoring and refresh methods
    # ------------------------------------------------------------------------------- #

    def _should_refresh_session(self):
        """
        Check if the session should be refreshed based on age and other factors
        """
        current_time = time.time()
        session_age = current_time - self.session_start_time

        # Refresh if session is older than the configured interval
        if session_age > self.session_refresh_interval:
            return True

        # Refresh if we've had recent 403 errors
        if self.last_403_time > 0 and (current_time - self.last_403_time) < 60:
            return True

        return False

    def _refresh_session(self, url):
        """
        Refresh the session by clearing cookies and re-establishing connection
        """
        try:
            if self.debug:
                print('Refreshing session due to staleness or 403 errors...')

            # Clear existing Cloudflare cookies
            self._clear_cloudflare_cookies()

            # Reset session tracking (but NOT the retry count yet)
            self.session_start_time = time.time()
            self.request_count = 0

            # Generate new user agent to avoid fingerprint detection
            if hasattr(self, 'user_agent'):
                self.user_agent.loadUserAgent()
                self.headers.update(self.user_agent.headers)

            # Make a simple request to re-establish session
            try:
                from urllib.parse import urlparse
                parsed_url = urlparse(url)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

                # Make a lightweight request to trigger challenge solving
                test_response = super(CloudScraper, self).get(base_url, timeout=30)

                if self.debug:
                    print(f'Session refresh request status: {test_response.status_code}')

                # Only return True if we got a successful response
                success = test_response.status_code in [200, 301, 302, 304]

                if success and self.debug:
                    print('✅ Session refresh successful')
                elif not success and self.debug:
                    print(f'❌ Session refresh failed with status: {test_response.status_code}')

                return success

            except Exception as e:
                if self.debug:
                    print(f'❌ Session refresh failed: {e}')
                return False

        except Exception as e:
            if self.debug:
                print(f'❌ Error during session refresh: {e}')
            return False

    def _clear_cloudflare_cookies(self):
        """
        Clear Cloudflare-specific cookies to force re-authentication
        """
        cf_cookie_names = ['cf_clearance', 'cf_chl_2', 'cf_chl_prog', 'cf_chl_rc_ni', 'cf_turnstile', '__cf_bm']

        for cookie_name in cf_cookie_names:
            # Remove cookies for all domains
            for domain in list(self.cookies.list_domains()):
                try:
                    self.cookies.clear(domain, '/', cookie_name)
                except:
                    pass

        if self.debug:
            print('Cleared Cloudflare cookies for session refresh')

    def _apply_request_throttling(self):
        """
        Apply request throttling to prevent TLS blocking from concurrent requests
        """
        current_time = time.time()

        # Wait for minimum interval between requests
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            if self.debug:
                print(f'⏱️ Request throttling: sleeping {sleep_time:.2f}s')
            time.sleep(sleep_time)

        # Wait if too many concurrent requests
        while self.current_concurrent_requests >= self.max_concurrent_requests:
            if self.debug:
                print(f'🚦 Concurrent request limit reached ({self.current_concurrent_requests}/{self.max_concurrent_requests}), waiting...')
            time.sleep(0.1)

        self.last_request_time = time.time()

    def _rotate_tls_cipher_suite(self):
        """
        Rotate TLS cipher suites to avoid detection patterns
        """
        if not hasattr(self, 'user_agent') or not hasattr(self.user_agent, 'cipherSuite'):
            return

        # Get available cipher suites for current browser
        browser_name = getattr(self.user_agent, 'browser', 'chrome')

        try:
            # Get cipher suites from browsers.json
            import json
            import os
            browsers_file = os.path.join(os.path.dirname(__file__), 'user_agent', 'browsers.json')

            with open(browsers_file, 'r') as f:
                browsers_data = json.load(f)

            available_ciphers = browsers_data.get('cipherSuite', {}).get(browser_name, [])

            if available_ciphers and len(available_ciphers) > 1:
                # Rotate through cipher suites
                self._cipher_rotation_count += 1
                cipher_index = self._cipher_rotation_count % len(available_ciphers)

                # Use a subset of ciphers to create variation
                num_ciphers = min(8, len(available_ciphers))  # Use up to 8 ciphers
                start_index = cipher_index % (len(available_ciphers) - num_ciphers + 1)
                selected_ciphers = available_ciphers[start_index:start_index + num_ciphers]

                new_cipher_suite = ':'.join(selected_ciphers)

                if new_cipher_suite != self.cipherSuite:
                    self.cipherSuite = new_cipher_suite

                    # Update the HTTPS adapter with new cipher suite
                    self.mount(
                        'https://',
                        CipherSuiteAdapter(
                            cipherSuite=self.cipherSuite,
                            ecdhCurve=self.ecdhCurve,
                            server_hostname=self.server_hostname,
                            source_address=self.source_address,
                            ssl_context=self.ssl_context
                        )
                    )

                    if self.debug:
                        print(f'🔐 Rotated TLS cipher suite (rotation #{self._cipher_rotation_count})')
                        print(f'    Using {len(selected_ciphers)} ciphers starting from index {start_index}')

        except Exception as e:
            if self.debug:
                print(f'⚠️ TLS cipher rotation failed: {e}')

    # ------------------------------------------------------------------------------- #

    @classmethod
    def create_scraper(cls, sess=None, **kwargs):
        """
        Convenience function for creating a ready-to-go CloudScraper object.

        Additional parameters:
        - rotating_proxies: List of proxy URLs or dict mapping URL schemes to proxy URLs
        - proxy_options: Dict with proxy configuration options
            - rotation_strategy: Strategy for rotating proxies ('sequential', 'random', or 'smart')
            - ban_time: Time in seconds to ban a proxy after a failure
        - enable_stealth: Whether to enable stealth mode (default: True)
        - stealth_options: Dict with stealth mode configuration options
            - min_delay: Minimum delay between requests in seconds
            - max_delay: Maximum delay between requests in seconds
            - human_like_delays: Whether to add random delays between requests
            - randomize_headers: Whether to randomize headers
            - browser_quirks: Whether to apply browser-specific quirks
        - session_refresh_interval: Time in seconds after which to refresh session (default: 3600)
        - auto_refresh_on_403: Whether to automatically refresh session on 403 errors (default: True)
        - max_403_retries: Maximum number of 403 retry attempts (default: 3)
        - min_request_interval: Minimum time in seconds between requests (default: 1.0)
        - max_concurrent_requests: Maximum number of concurrent requests (default: 1)
        - rotate_tls_ciphers: Whether to rotate TLS cipher suites to avoid detection (default: True)
        - disableCloudflareV3: Whether to disable Cloudflare v3 JavaScript VM challenge handling (default: False)
        - disableTurnstile: Whether to disable Cloudflare Turnstile challenge handling (default: False)
        """
        scraper = cls(**kwargs)

        if sess:
            for attr in ['auth', 'cert', 'cookies', 'headers', 'hooks', 'params', 'proxies', 'data']:
                val = getattr(sess, attr, None)
                if val is not None:
                    setattr(scraper, attr, val)

        return scraper

    # ------------------------------------------------------------------------------- #
    # Functions for integrating cloudscraper with other applications and scripts
    # ------------------------------------------------------------------------------- #

    @classmethod
    def get_tokens(cls, url, **kwargs):
        """
        Get Cloudflare tokens for a URL

        Additional parameters:
        - rotating_proxies: List of proxy URLs or dict mapping URL schemes to proxy URLs
        - proxy_options: Dict with proxy configuration options
        - enable_stealth: Whether to enable stealth mode (default: True)
        - stealth_options: Dict with stealth mode configuration options
        - session_refresh_interval: Time in seconds after which to refresh session (default: 3600)
        - auto_refresh_on_403: Whether to automatically refresh session on 403 errors (default: True)
        - max_403_retries: Maximum number of 403 retry attempts (default: 3)
        - disableCloudflareV3: Whether to disable Cloudflare v3 JavaScript VM challenge handling (default: False)
        - disableTurnstile: Whether to disable Cloudflare Turnstile challenge handling (default: False)
        """
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
                    'source_address',
                    'requestPreHook',
                    'requestPostHook',
                    'rotating_proxies',
                    'proxy_options',
                    'enable_stealth',
                    'stealth_options',
                    'session_refresh_interval',
                    'auto_refresh_on_403',
                    'max_403_retries',
                    'disableCloudflareV3',
                    'disableTurnstile'
                ] if field in kwargs
            }
        )

        try:
            resp = scraper.get(url, **kwargs)
            resp.raise_for_status()
        except Exception as e:
            logging.error(f'"{url}" returned an error. Could not collect tokens. Error: {str(e)}')
            raise

        domain = urlparse(resp.url).netloc
        cookie_domain = None

        for d in scraper.cookies.list_domains():
            if d.startswith('.') and d in (f'.{domain}'):
                cookie_domain = d
                break
        else:
            # Try without the dot prefix
            for d in scraper.cookies.list_domains():
                if d == domain:
                    cookie_domain = d
                    break
            else:
                cls.simpleException(
                    cls,
                    CloudflareIUAMError,
                    "Unable to find Cloudflare cookies. Does the site actually "
                    "have Cloudflare IUAM (I'm Under Attack Mode) enabled?"
                )

        # Get all Cloudflare cookies
        cf_cookies = {}
        for cookie_name in ['cf_clearance', 'cf_chl_2', 'cf_chl_prog', 'cf_chl_rc_ni', 'cf_turnstile']:
            cookie_value = scraper.cookies.get(cookie_name, '', domain=cookie_domain)
            if cookie_value:
                cf_cookies[cookie_name] = cookie_value

        return (
            cf_cookies,
            scraper.headers['User-Agent']
        )

    # ------------------------------------------------------------------------------- #

    @classmethod
    def get_cookie_string(cls, url, **kwargs):
        """
        Convenience function for building a Cookie HTTP header value.

        Additional parameters:
        - rotating_proxies: List of proxy URLs or dict mapping URL schemes to proxy URLs
        - proxy_options: Dict with proxy configuration options
        - enable_stealth: Whether to enable stealth mode (default: True)
        - stealth_options: Dict with stealth mode configuration options
        - session_refresh_interval: Time in seconds after which to refresh session (default: 3600)
        - auto_refresh_on_403: Whether to automatically refresh session on 403 errors (default: True)
        - max_403_retries: Maximum number of 403 retry attempts (default: 3)
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
session = CloudScraper.create_scraper
get_tokens = CloudScraper.get_tokens
get_cookie_string = CloudScraper.get_cookie_string
