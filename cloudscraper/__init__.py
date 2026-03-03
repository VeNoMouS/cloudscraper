# -*- coding: utf-8 -*-
"""
cloudscraper
============

Enhanced Python library to bypass Cloudflare's anti-bot page with support
for v1, v2, v3 challenges, Turnstile, proxy rotation, and stealth mode.

Example:
    >>> import cloudscraper
    >>> scraper = cloudscraper.create_scraper()
    >>> response = scraper.get("https://example.com")
    >>> print(response.text)
"""

from __future__ import annotations

import copyreg
import logging
import ssl
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from requests.sessions import Session

# Try to import brotli, but don't fail if not available
try:
    import brotli
except ImportError:
    brotli = None

from requests_toolbelt.utils import dump

# Import constants
from .constants import (
    DEFAULT_ECDH_CURVE,
    DEFAULT_INTERPRETER,
    DEFAULT_MAX_403_RETRIES,
    DEFAULT_MAX_CONCURRENT_REQUESTS,
    DEFAULT_MIN_REQUEST_INTERVAL,
    DEFAULT_SESSION_REFRESH_INTERVAL,
    DEFAULT_SOLVE_DEPTH,
    CLOUDFLARE_COOKIE_NAMES,
    CLOUDFLARE_CHALLENGE_STATUS_CODES,
    IS_OPENSSL_SUPPORTED,
)

# Import exceptions
from .exceptions import (
    CloudflareLoopProtection,
    CloudflareIUAMError,
    CloudflareChallengeError,
    CloudflareTurnstileError,
    CloudflareV3Error,
)

# Import modules
from .cloudflare import CloudflareV1
from .cloudflare_v2 import CloudflareV2
from .cloudflare_v3 import CloudflareV3
from .turnstile import CloudflareTurnstile
from .user_agent import User_Agent
from .proxy_manager import ProxyManager
from .stealth import StealthMode
from .session_manager import SessionManager
from .request_throttler import RequestThrottler


__version__ = '3.0.0'


# -------------------------------------------------------------------------------
# SSL/TLS Configuration
# -------------------------------------------------------------------------------

class CipherSuiteAdapter(HTTPAdapter):
    """Custom HTTP adapter with configurable TLS cipher suites."""
    
    __attrs__: List[str] = [
        'ssl_context', 'max_retries', 'config',
        '_pool_connections', '_pool_maxsize', '_pool_block', 'source_address'
    ]
    
    def __init__(
        self,
        cipherSuite: Optional[str] = None,
        ecdhCurve: str = DEFAULT_ECDH_CURVE,
        server_hostname: Optional[str] = None,
        source_address: Optional[Union[str, Tuple[str, int]]] = None,
        ssl_context: Optional[ssl.SSLContext] = None,
        **kwargs: Any
    ) -> None:
        self.cipherSuite = cipherSuite
        self.ecdhCurve = ecdhCurve
        self.server_hostname = server_hostname
        self.source_address = source_address
        
        if source_address:
            if isinstance(source_address, str):
                self.source_address = (source_address, 0)
            if not isinstance(self.source_address, tuple):
                raise TypeError("source_address must be IP address string or (ip, port) tuple")
        
        if not ssl_context:
            self.ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            self.ssl_context.orig_wrap_socket = self.ssl_context.wrap_socket
            self.ssl_context.wrap_socket = self.wrap_socket
            
            if server_hostname:
                self.ssl_context.server_hostname = server_hostname
            
            if cipherSuite:
                self.ssl_context.set_ciphers(cipherSuite)
            self.ssl_context.set_ecdh_curve(ecdhCurve)
            self.ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            self.ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
        else:
            self.ssl_context = ssl_context
        
        super().__init__(**kwargs)
    
    def wrap_socket(self, *args: Any, **kwargs: Any) -> Any:
        if hasattr(self.ssl_context, 'server_hostname') and self.ssl_context.server_hostname:
            kwargs['server_hostname'] = self.ssl_context.server_hostname
            self.ssl_context.check_hostname = False
        else:
            self.ssl_context.check_hostname = True
        return self.ssl_context.orig_wrap_socket(*args, **kwargs)
    
    def init_poolmanager(self, *args: Any, **kwargs: Any) -> Any:
        kwargs['ssl_context'] = self.ssl_context
        kwargs['source_address'] = self.source_address
        return super().init_poolmanager(*args, **kwargs)
    
    def proxy_manager_for(self, *args: Any, **kwargs: Any) -> Any:
        kwargs['ssl_context'] = self.ssl_context
        kwargs['source_address'] = self.source_address
        return super().proxy_manager_for(*args, **kwargs)


# -------------------------------------------------------------------------------
# Main CloudScraper Class
# -------------------------------------------------------------------------------

class CloudScraper(Session):
    """
    Main class for making HTTP requests that bypass Cloudflare protection.
    
    Inherits from requests.Session to provide full compatibility with the
    requests library while automatically handling Cloudflare challenges.
    """
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Configuration options
        self.debug: bool = kwargs.pop('debug', False)
        
        # Challenge handling options
        self.disableCloudflareV1: bool = kwargs.pop('disableCloudflareV1', False)
        self.disableCloudflareV2: bool = kwargs.pop('disableCloudflareV2', False)
        self.disableCloudflareV3: bool = kwargs.pop('disableCloudflareV3', False)
        self.disableTurnstile: bool = kwargs.pop('disableTurnstile', False)
        self.delay: Optional[float] = kwargs.pop('delay', None)
        self.captcha: Dict[str, Any] = kwargs.pop('captcha', {})
        self.doubleDown: bool = kwargs.pop('doubleDown', True)
        self.interpreter: str = kwargs.pop('interpreter', DEFAULT_INTERPRETER)
        self.solveDepth: int = kwargs.pop('solveDepth', DEFAULT_SOLVE_DEPTH)
        
        # Request hooks
        self.requestPreHook: Optional[Callable] = kwargs.pop('requestPreHook', None)
        self.requestPostHook: Optional[Callable] = kwargs.pop('requestPostHook', None)
        
        # TLS/SSL options
        self.cipherSuite: Optional[str] = kwargs.pop('cipherSuite', None)
        self.ecdhCurve: str = kwargs.pop('ecdhCurve', DEFAULT_ECDH_CURVE)
        self.source_address = kwargs.pop('source_address', None)
        self.server_hostname = kwargs.pop('server_hostname', None)
        self.ssl_context = kwargs.pop('ssl_context', None)
        
        # Compression options
        self.allow_brotli: bool = kwargs.pop('allow_brotli', 'brotli' in sys.modules)
        
        # User agent handling
        browser_config = kwargs.pop('browser', None)
        self.user_agent: User_Agent = User_Agent(allow_brotli=self.allow_brotli, browser=browser_config)
        
        # Challenge solving depth
        self._solveDepthCnt: int = 0
        
        # Session management
        self.session_manager: SessionManager = SessionManager(
            cloudscraper=self,
            session_refresh_interval=kwargs.pop('session_refresh_interval', DEFAULT_SESSION_REFRESH_INTERVAL),
            auto_refresh_on_403=kwargs.pop('auto_refresh_on_403', True),
            max_403_retries=kwargs.pop('max_403_retries', DEFAULT_MAX_403_RETRIES)
        )
        
        # Request throttling
        self.request_throttler: RequestThrottler = RequestThrottler(
            cloudscraper=self,
            min_request_interval=kwargs.pop('min_request_interval', DEFAULT_MIN_REQUEST_INTERVAL),
            max_concurrent_requests=kwargs.pop('max_concurrent_requests', DEFAULT_MAX_CONCURRENT_REQUESTS),
            rotate_tls_ciphers=kwargs.pop('rotate_tls_ciphers', True)
        )
        
        # Proxy management
        proxy_options = kwargs.pop('proxy_options', {})
        self.proxy_manager: ProxyManager = ProxyManager(
            proxies=kwargs.pop('rotating_proxies', None),
            proxy_rotation_strategy=proxy_options.get('rotation_strategy', 'sequential'),
            ban_time=proxy_options.get('ban_time', 300)
        )
        
        # Stealth mode
        self.stealth_mode: StealthMode = StealthMode(self)
        self.enable_stealth: bool = kwargs.pop('enable_stealth', True)
        
        # Configure stealth options
        stealth_options = kwargs.pop('stealth_options', {})
        if stealth_options:
            if 'min_delay' in stealth_options and 'max_delay' in stealth_options:
                self.stealth_mode.set_delay_range(stealth_options['min_delay'], stealth_options['max_delay'])
            self.stealth_mode.enable_human_like_delays(stealth_options.get('human_like_delays', True))
            self.stealth_mode.enable_randomize_headers(stealth_options.get('randomize_headers', True))
            self.stealth_mode.enable_browser_quirks(stealth_options.get('browser_quirks', True))
        
        # Initialize parent session
        super().__init__(*args, **kwargs)
        
        # Set up User-Agent
        if 'requests' in self.headers.get('User-Agent', ''):
            self.headers = self.user_agent.headers
            if not self.cipherSuite:
                self.cipherSuite = self.user_agent.cipherSuite
        
        # Convert cipher suite list to string
        if isinstance(self.cipherSuite, list):
            self.cipherSuite = ':'.join(self.cipherSuite)
        
        # Mount HTTPS adapter
        self.mount('https://', CipherSuiteAdapter(
            cipherSuite=self.cipherSuite,
            ecdhCurve=self.ecdhCurve,
            server_hostname=self.server_hostname,
            source_address=self.source_address,
            ssl_context=self.ssl_context
        ))
        
        # Initialize challenge handlers
        self.cloudflare_v1 = CloudflareV1(self)
        self.cloudflare_v2 = CloudflareV2(self)
        self.cloudflare_v3 = CloudflareV3(self)
        self.turnstile = CloudflareTurnstile(self)
        
        # Allow pickle serialization
        copyreg.pickle(ssl.SSLContext, lambda obj: (obj.__class__, (obj.protocol,)))
    
    def __getstate__(self) -> Dict[str, Any]:
        return self.__dict__
    
    def perform_request(self, method: str, url: str, *args: Any, **kwargs: Any) -> requests.Response:
        return super().request(method, url, *args, **kwargs)
    
    @staticmethod
    def simpleException(exception: type, msg: str) -> None:
        sys.tracebacklimit = 0
        raise exception(msg)
    
    @staticmethod
    def debugRequest(req: requests.PreparedRequest) -> None:
        try:
            print(dump.dump_all(req).decode('utf-8', errors='backslashreplace'))
        except ValueError as e:
            print(f"Debug Error: {getattr(e, 'message', e)}")
    
    def decodeBrotli(self, resp: requests.Response) -> requests.Response:
        if hasattr(requests.packages, 'urllib3'):
            urllib3_version = getattr(requests.packages.urllib3, '__version__', '0.0.0')
            if urllib3_version < '1.25.1' and resp.headers.get('Content-Encoding') == 'br':
                if self.allow_brotli and resp._content and brotli:
                    resp._content = brotli.decompress(resp.content)
                elif not self.allow_brotli:
                    logging.warning(f"You're running urllib3 {urllib3_version}, Brotli content detected, but option allow_brotli is set to False.")
        return resp
    
    def request(self, method: str, url: str, *args: Any, **kwargs: Any) -> requests.Response:
        # Apply request throttling
        self.request_throttler.acquire()
        
        # Check if session needs refresh
        if self.session_manager.should_refresh():
            self.session_manager.refresh(url)
        
        # Handle proxy rotation
        if not kwargs.get('proxies') and hasattr(self, 'proxy_manager') and self.proxy_manager.proxies:
            kwargs['proxies'] = self.proxy_manager.get_proxy()
        elif kwargs.get('proxies') and kwargs.get('proxies') != self.proxies:
            self.proxies = kwargs.get('proxies')
        
        # Apply stealth techniques
        if self.enable_stealth:
            kwargs = self.stealth_mode.apply_stealth_techniques(method, url, **kwargs)
        
        # Increment request count
        self.session_manager.increment_request_count()
        
        # Apply pre-hook
        if self.requestPreHook:
            method, url, args, kwargs = self.requestPreHook(self, method, url, *args, **kwargs)
        
        # Make request
        try:
            response = self.decodeBrotli(self.perform_request(method, url, *args, **kwargs))
            
            if kwargs.get('proxies') and hasattr(self, 'proxy_manager'):
                self.proxy_manager.report_success(kwargs['proxies'])
        
        except (requests.exceptions.ProxyError, requests.exceptions.ConnectionError) as e:
            if kwargs.get('proxies') and hasattr(self, 'proxy_manager'):
                self.proxy_manager.report_failure(kwargs['proxies'])
            self.request_throttler.release()
            raise e
        except Exception as e:
            self.request_throttler.release()
            raise e
        
        # Debug
        if self.debug:
            self.debugRequest(response)
        
        # Apply post-hook
        if self.requestPostHook:
            new_response = self.requestPostHook(self, response)
            if response != new_response:
                response = new_response
                if self.debug:
                    self.debugRequest(response)
        
        # Check for loop protection
        if self._solveDepthCnt >= self.solveDepth:
            self.simpleException(CloudflareLoopProtection, f"!!Loop Protection!! We have tried to solve {self._solveDepthCnt} time(s) in a row.")
        
        # Handle challenges
        response = self._handle_challenges(response, **kwargs)
        
        # Reset on success
        self.session_manager.reset_on_success(response)
        
        # Handle 403 errors
        if response.status_code == 403:
            retry_response = self.session_manager.handle_403(response, method, url, *args, **kwargs)
            if retry_response:
                return retry_response
        
        self.request_throttler.release()
        return response
    
    def _handle_challenges(self, response: requests.Response, **kwargs: Any) -> requests.Response:
        # Check Turnstile challenge first
        if not self.disableTurnstile:
            if self.turnstile.is_challenge(response):
                if self.debug:
                    print('Detected a Cloudflare Turnstile challenge.')
                self._solveDepthCnt += 1
                return self.turnstile.handle_challenge(response, **kwargs)
        
        # Check v3 challenge
        if not self.disableCloudflareV3:
            if self.cloudflare_v3.is_challenge(response):
                if self.debug:
                    print('Detected a Cloudflare v3 JavaScript VM challenge.')
                self._solveDepthCnt += 1
                return self.cloudflare_v3.handle_challenge(response, **kwargs)
        
        # Check v2 challenge
        if not self.disableCloudflareV2:
            if self.cloudflare_v2.is_challenge(response):
                if self.debug:
                    print('Detected a Cloudflare v2 challenge.')
                self._solveDepthCnt += 1
                return self.cloudflare_v2.handle_challenge(response, **kwargs)
        
        # Check v1 challenge
        if not self.disableCloudflareV1:
            if self.cloudflare_v1.is_challenge(response):
                if self.debug:
                    print('Detected a Cloudflare v1 challenge.')
                self._solveDepthCnt += 1
                return self.cloudflare_v1.handle_challenge(response, **kwargs)
        
        # Reset counter if no challenge
        if not response.is_redirect and response.status_code not in CLOUDFLARE_CHALLENGE_STATUS_CODES:
            self._solveDepthCnt = 0
        
        return response
    
    @classmethod
    def create_scraper(cls, sess: Optional[Session] = None, **kwargs: Any) -> 'CloudScraper':
        scraper = cls(**kwargs)
        if sess:
            for attr in ['auth', 'cert', 'cookies', 'headers', 'hooks', 'params', 'proxies', 'data']:
                val = getattr(sess, attr, None)
                if val is not None:
                    setattr(scraper, attr, val)
        return scraper
    
    @classmethod
    def get_tokens(cls, url: str, **kwargs: Any) -> Tuple[Dict[str, str], str]:
        valid_fields = [
            'allow_brotli', 'browser', 'debug', 'delay', 'doubleDown',
            'captcha', 'interpreter', 'source_address', 'requestPreHook',
            'requestPostHook', 'rotating_proxies', 'proxy_options',
            'enable_stealth', 'stealth_options', 'session_refresh_interval',
            'auto_refresh_on_403', 'max_403_retries', 'disableCloudflareV3',
            'disableTurnstile'
        ]
        
        scraper = cls.create_scraper(**{field: kwargs.pop(field, None) for field in valid_fields if field in kwargs})
        
        try:
            resp = scraper.get(url, **kwargs)
            resp.raise_for_status()
        except Exception as e:
            logging.error(f'"{url}" returned an error. Could not collect tokens. Error: {str(e)}')
            raise
        
        parsed_url = urlparse(resp.url)
        domain = parsed_url.netloc
        cookie_domain = None
        
        for d in scraper.cookies.list_domains():
            if d.startswith('.') and d in (f'.{domain}', domain):
                cookie_domain = d
                break
        else:
            for d in scraper.cookies.list_domains():
                if d == domain:
                    cookie_domain = d
                    break
            else:
                cls.simpleException(CloudflareIUAMError, "Unable to find Cloudflare cookies.")
        
        cf_cookies = {}
        for cookie_name in CLOUDFLARE_COOKIE_NAMES:
            cookie_value = scraper.cookies.get(cookie_name, '', domain=cookie_domain)
            if cookie_value:
                cf_cookies[cookie_name] = cookie_value
        
        return cf_cookies, scraper.headers.get('User-Agent', '')
    
    @classmethod
    def get_cookie_string(cls, url: str, **kwargs: Any) -> Tuple[str, str]:
        tokens, user_agent = cls.get_tokens(url, **kwargs)
        return '; '.join('='.join(pair) for pair in tokens.items()), user_agent


# Module exports
create_scraper = CloudScraper.create_scraper
session = CloudScraper.create_scraper
get_tokens = CloudScraper.get_tokens
get_cookie_string = CloudScraper.get_cookie_string


# OpenSSL version check
if not IS_OPENSSL_SUPPORTED:
    print(f"DEPRECATION: The OpenSSL being used ({ssl.OPENSSL_VERSION}) does not meet the minimum supported version (>= OpenSSL 1.1.1). You may encounter unexpected Captcha or cloudflare 1020 blocks.")
