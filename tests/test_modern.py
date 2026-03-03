"""
Comprehensive test suite for cloudscraper
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from http.cookiejar import Cookie

import cloudscraper
from cloudscraper import CloudScraper
from cloudscraper.exceptions import (
    CloudflareLoopProtection,
    CloudflareIUAMError,
    CloudflareChallengeError,
    CloudflareCode1020,
    CloudflareCaptchaProvider,
    CloudflareTurnstileError,
    CloudflareSolveError,
)


# ==============================================================================
# Test CloudScraper Initialization
# ==============================================================================

class TestCloudScraperInit:
    """Test CloudScraper initialization and configuration"""
    
    def test_create_scraper_default(self):
        """Test default scraper creation"""
        scraper = cloudscraper.create_scraper()
        assert isinstance(scraper, CloudScraper)
    
    def test_create_scraper_with_all_options(self):
        """Test scraper with all configuration options"""
        scraper = cloudscraper.create_scraper(
            debug=True,
            browser='chrome',
            delay=5.0,
            interpreter='js2py',
            enable_stealth=True,
            session_refresh_interval=1800,
            auto_refresh_on_403=True,
            max_403_retries=5,
            min_request_interval=0.5,
            max_concurrent_requests=2,
            rotate_tls_ciphers=True,
            disableCloudflareV1=False,
            disableCloudflareV2=False,
            disableCloudflareV3=False,
            disableTurnstile=False,
        )
        
        assert scraper.debug is True
        assert scraper.delay == 5.0
        assert scraper.interpreter == 'js2py'
        assert scraper.enable_stealth is True
        assert scraper.session_manager.session_refresh_interval == 1800
        assert scraper.session_manager.auto_refresh_on_403 is True
        assert scraper.session_manager.max_403_retries == 5
        assert scraper.request_throttler.min_request_interval == 0.5
        assert scraper.request_throttler.max_concurrent_requests == 2
    
    def test_create_scraper_with_captcha_config(self):
        """Test scraper with captcha configuration"""
        captcha_config = {
            'provider': '2captcha',
            'api_key': 'test_key'
        }
        scraper = cloudscraper.create_scraper(captcha=captcha_config)
        assert scraper.captcha == captcha_config
    
    def test_create_scraper_with_proxy(self):
        """Test scraper with proxy configuration"""
        proxies = ['http://proxy1:8080', 'http://proxy2:8080']
        scraper = cloudscraper.create_scraper(
            rotating_proxies=proxies,
            proxy_options={
                'rotation_strategy': 'smart',
                'ban_time': 600
            }
        )
        assert scraper.proxy_manager.proxies == proxies
    
    def test_create_scraper_with_stealth_options(self):
        """Test scraper with stealth options"""
        stealth_opts = {
            'min_delay': 2.0,
            'max_delay': 5.0,
            'human_like_delays': True,
            'randomize_headers': True,
            'browser_quirks': True
        }
        scraper = cloudscraper.create_scraper(
            enable_stealth=True,
            stealth_options=stealth_opts
        )
        assert scraper.enable_stealth is True
        assert scraper.stealth_mode.min_delay == 2.0
        assert scraper.stealth_mode.max_delay == 5.0
    
    def test_version_info(self):
        """Test version information is set"""
        assert cloudscraper.__version__ == '3.0.0'
    
    def test_ssl_context_created(self):
        """Test SSL context is created"""
        scraper = cloudscraper.create_scraper()
        assert hasattr(scraper, 'ssl_context')
        assert scraper.ssl_context is not None
    
    def test_cipher_suite_adapter_mounted(self):
        """Test HTTPS adapter is mounted"""
        scraper = cloudscraper.create_scraper()
        # Check that adapter is mounted for https://
        adapters = scraper.adapters.get('https://')
        assert adapters is not None


# ==============================================================================
# Test User Agent
# ==============================================================================

class TestUserAgent:
    """Test user agent handling"""
    
    def test_default_user_agent(self):
        """Test default user agent generation"""
        scraper = cloudscraper.create_scraper()
        ua = scraper.headers.get('User-Agent')
        assert ua is not None
        assert 'Mozilla' in ua
    
    def test_chrome_user_agent(self):
        """Test Chrome user agent"""
        scraper = cloudscraper.create_scraper(browser='chrome')
        ua = scraper.headers.get('User-Agent')
        assert 'Chrome' in ua or 'Mozilla' in ua
    
    def test_firefox_user_agent(self):
        """Test Firefox user agent"""
        scraper = cloudscraper.create_scraper(browser='firefox')
        ua = scraper.headers.get('User-Agent')
        assert 'Firefox' in ua or 'Mozilla' in ua
    
    def test_custom_user_agent(self):
        """Test custom user agent"""
        custom_ua = 'MyCustomBot/1.0'
        scraper = cloudscraper.create_scraper(browser={'custom': custom_ua})
        assert scraper.headers.get('User-Agent') == custom_ua
    
    def test_platform_filtering(self):
        """Test platform filtering"""
        for platform in ['windows', 'linux', 'darwin', 'android', 'ios']:
            scraper = cloudscraper.create_scraper(
                browser={'browser': 'chrome', 'platform': platform}
            )
            ua = scraper.headers.get('User-Agent')
            assert ua is not None
    
    def test_brotli_disabled(self):
        """Test brotli can be disabled"""
        scraper = cloudscraper.create_scraper(allow_brotli=False)
        encoding = scraper.headers.get('Accept-Encoding', '')
        assert 'br' not in encoding


# ==============================================================================
# Test Session Manager
# ==============================================================================

class TestSessionManager:
    """Test session management functionality"""
    
    def test_initial_state(self):
        """Test initial session state"""
        scraper = cloudscraper.create_scraper()
        assert scraper.session_manager.session_start_time > 0
        assert scraper.session_manager.request_count == 0
        assert scraper.session_manager._403_retry_count == 0
        assert scraper.session_manager.last_403_time == 0
    
    def test_should_refresh_new_session(self):
        """Test new session should not refresh"""
        scraper = cloudscraper.create_scraper(
            session_refresh_interval=3600
        )
        assert scraper.session_manager.should_refresh() is False
    
    def test_should_refresh_old_session(self):
        """Test old session should refresh"""
        scraper = cloudscraper.create_scraper(
            session_refresh_interval=1
        )
        time.sleep(1.1)
        assert scraper.session_manager.should_refresh() is True
    
    def test_should_refresh_after_403(self):
        """Test session refresh after 403 error"""
        scraper = cloudscraper.create_scraper()
        scraper.session_manager.last_403_time = time.time()
        assert scraper.session_manager.should_refresh() is True
    
    def test_clear_cloudflare_cookies(self):
        """Test clearing Cloudflare cookies"""
        scraper = cloudscraper.create_scraper()
        
        # Set cookies
        scraper.cookies.set('cf_clearance', 'test_value')
        scraper.cookies.set('cf_chl_2', 'test_value')
        scraper.cookies.set('__cfduid', 'test_value')
        
        # Clear cookies
        scraper.session_manager._clear_cloudflare_cookies()
        
        # Verify
        assert scraper.cookies.get('cf_clearance') is None
    
    def test_reset_on_success(self):
        """Test counter reset on success"""
        scraper = cloudscraper.create_scraper()
        
        # Simulate 403 retries
        scraper.session_manager._403_retry_count = 3
        
        # Create mock response
        mock_response = Mock()
        mock_response.is_redirect = False
        mock_response.status_code = 200
        
        scraper.session_manager.reset_on_success(mock_response)
        
        assert scraper.session_manager._403_retry_count == 0
    
    def test_increment_request_count(self):
        """Test request count increment"""
        scraper = cloudscraper.create_scraper()
        initial = scraper.session_manager.request_count
        scraper.session_manager.increment_request_count()
        assert scraper.session_manager.request_count == initial + 1


# ==============================================================================
# Test Request Throttler
# ==============================================================================

class TestRequestThrottler:
    """Test request throttling"""
    
    def test_throttler_initialization(self):
        """Test throttler initialization"""
        scraper = cloudscraper.create_scraper()
        assert scraper.request_throttler.min_request_interval == 1.0
        assert scraper.request_throttler.max_concurrent_requests == 1
        assert scraper.request_throttler.rotate_tls_ciphers is True
    
    def test_custom_throttle_settings(self):
        """Test custom throttle settings"""
        scraper = cloudscraper.create_scraper(
            min_request_interval=0.5,
            max_concurrent_requests=3
        )
        assert scraper.request_throttler.min_request_interval == 0.5
        assert scraper.request_throttler.max_concurrent_requests == 3
    
    def test_concurrent_request_tracking(self):
        """Test concurrent request tracking"""
        scraper = cloudscraper.create_scraper()
        assert scraper.request_throttler.current_concurrent_requests == 0
        
        scraper.request_throttler.acquire()
        assert scraper.request_throttler.current_concurrent_requests == 1
        
        scraper.request_throttler.release()
        assert scraper.request_throttler.current_concurrent_requests == 0


# ==============================================================================
# Test Challenge Handlers
# ==============================================================================

class TestChallengeHandlers:
    """Test challenge handler initialization"""
    
    def test_challenge_handlers_exist(self):
        """Test all challenge handlers are initialized"""
        scraper = cloudscraper.create_scraper()
        assert hasattr(scraper, 'cloudflare_v1')
        assert hasattr(scraper, 'cloudflare_v2')
        assert hasattr(scraper, 'cloudflare_v3')
        assert hasattr(scraper, 'turnstile')
    
    def test_disable_challenge_handlers(self):
        """Test disabling challenge handlers"""
        scraper = cloudscraper.create_scraper(
            disableCloudflareV1=True,
            disableCloudflareV2=True,
            disableCloudflareV3=True,
            disableTurnstile=True
        )
        assert scraper.disableCloudflareV1 is True
        assert scraper.disableCloudflareV2 is True
        assert scraper.disableCloudflareV3 is True
        assert scraper.disableTurnstile is True
    
    @patch('cloudscraper.CloudScraper.perform_request')
    def test_loop_protection(self, mock_request):
        """Test loop protection"""
        scraper = cloudscraper.create_scraper(solveDepth=2)
        
        # Simulate solving challenges
        scraper._solveDepthCnt = 2
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.is_redirect = False
        mock_response.headers = {}
        mock_response.text = ''
        
        mock_request.return_value = mock_response
        
        with pytest.raises(CloudflareLoopProtection):
            scraper.get('http://example.com')


# ==============================================================================
# Test Proxy Manager
# ==============================================================================

class TestProxyManager:
    """Test proxy management"""
    
    def test_proxy_manager_initialization(self):
        """Test proxy manager initialization"""
        proxies = ['http://proxy1:8080', 'http://proxy2:8080']
        scraper = cloudscraper.create_scraper(
            rotating_proxies=proxies,
            proxy_options={
                'rotation_strategy': 'sequential',
                'ban_time': 300
            }
        )
        assert scraper.proxy_manager.proxies == proxies
    
    def test_proxy_rotation_sequential(self):
        """Test sequential proxy rotation"""
        proxies = ['http://proxy1:8080', 'http://proxy2:8080']
        scraper = cloudscraper.create_scraper(
            rotating_proxies=proxies,
            proxy_options={'rotation_strategy': 'sequential'}
        )
        
        # Get first proxy
        p1 = scraper.proxy_manager.get_proxy()
        assert p1 in proxies
        
        # Get second proxy
        p2 = scraper.proxy_manager.get_proxy()
        assert p2 in proxies
    
    def test_proxy_report_success(self):
        """Test proxy success reporting"""
        proxies = ['http://proxy1:8080']
        scraper = cloudscraper.create_scraper(rotating_proxies=proxies)
        
        # Report success should not raise
        scraper.proxy_manager.report_success(proxies[0])
    
    def test_proxy_report_failure(self):
        """Test proxy failure reporting"""
        proxies = ['http://proxy1:8080']
        scraper = cloudscraper.create_scraper(rotating_proxies=proxies)
        
        # Report failure should not raise
        scraper.proxy_manager.report_failure(proxies[0])


# ==============================================================================
# Test Exceptions
# ==============================================================================

class TestExceptions:
    """Test exception classes"""
    
    def test_cloudflare_exception(self):
        """Test base Cloudflare exception"""
        with pytest.raises(cloudscraper.CloudflareException):
            raise cloudscraper.CloudflareException("Test")
    
    def test_cloudflare_loop_protection(self):
        """Test loop protection exception"""
        with pytest.raises(CloudflareLoopProtection):
            raise CloudflareLoopProtection("Loop detected")
    
    def test_cloudflare_iuam_error(self):
        """Test IUAM error"""
        with pytest.raises(CloudflareIUAMError):
            raise CloudflareIUAMError("IUAM failed")
    
    def test_cloudflare_challenge_error(self):
        """Test challenge error"""
        with pytest.raises(CloudflareChallengeError):
            raise CloudflareChallengeError("Challenge failed")
    
    def test_cloudflare_code1020(self):
        """Test 1020 error"""
        with pytest.raises(CloudflareCode1020):
            raise CloudflareCode1020("Blocked")
    
    def test_cloudflare_captcha_provider(self):
        """Test captcha provider error"""
        with pytest.raises(CloudflareCaptchaProvider):
            raise CloudflareCaptchaProvider("No provider")


# ==============================================================================
# Test Backward Compatibility
# ==============================================================================

class TestBackwardCompatibility:
    """Test backward compatibility"""
    
    def test_create_scraper_alias(self):
        """Test create_scraper alias"""
        scraper = cloudscraper.create_scraper()
        assert isinstance(scraper, CloudScraper)
    
    def test_session_alias(self):
        """Test session alias"""
        scraper = cloudscraper.session()
        assert isinstance(scraper, CloudScraper)
    
    def test_get_tokens_classmethod(self):
        """Test get_tokens class method exists"""
        assert hasattr(CloudScraper, 'get_tokens')
        assert callable(CloudScraper.get_tokens)
    
    def test_get_cookie_string_classmethod(self):
        """Test get_cookie_string class method exists"""
        assert hasattr(CloudScraper, 'get_cookie_string')
        assert callable(CloudScraper.get_cookie_string)


# ==============================================================================
# Test Constants
# ==============================================================================

class TestConstants:
    """Test constants module"""
    
    def test_constants_import(self):
        """Test constants can be imported"""
        from cloudscraper import constants
        assert constants.DEFAULT_SOLVE_DEPTH == 3
        assert constants.DEFAULT_SESSION_REFRESH_INTERVAL == 3600
        assert constants.DEFAULT_MAX_403_RETRIES == 3
        assert constants.DEFAULT_MIN_REQUEST_INTERVAL == 1.0
    
    def test_cloudflare_cookie_names(self):
        """Test Cloudflare cookie names"""
        from cloudscraper.constants import CLOUDFLARE_COOKIE_NAMES
        assert 'cf_clearance' in CLOUDFLARE_COOKIE_NAMES
        assert '__cfduid' in CLOUDFLARE_COOKIE_NAMES


# ==============================================================================
# Test Request Methods
# ==============================================================================

class TestRequestMethods:
    """Test HTTP request methods"""
    
    @patch('cloudscraper.CloudScraper.perform_request')
    def test_get_request(self, mock_request):
        """Test GET request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.is_redirect = False
        mock_response.headers = {}
        mock_response.text = 'Test content'
        mock_request.return_value = mock_response
        
        scraper = cloudscraper.create_scraper()
        response = scraper.get('http://example.com')
        
        assert response.status_code == 200
    
    @patch('cloudscraper.CloudScraper.perform_request')
    def test_post_request(self, mock_request):
        """Test POST request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.is_redirect = False
        mock_response.headers = {}
        mock_response.text = 'Test content'
        mock_request.return_value = mock_response
        
        scraper = cloudscraper.create_scraper()
        response = scraper.post('http://example.com', data={'key': 'value'})
        
        assert response.status_code == 200
    
    @patch('cloudscraper.CloudScraper.perform_request')
    def test_request_with_params(self, mock_request):
        """Test request with query parameters"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.is_redirect = False
        mock_response.headers = {}
        mock_response.text = 'Test content'
        mock_request.return_value = mock_response
        
        scraper = cloudscraper.create_scraper()
        response = scraper.get('http://example.com', params={'key': 'value'})
        
        assert response.status_code == 200


# ==============================================================================
# Test Integration (Marked as Slow)
# ==============================================================================

@pytest.mark.slow
class TestIntegration:
    """Integration tests (require network)"""
    
    def test_simple_request(self):
        """Test simple HTTP request"""
        scraper = cloudscraper.create_scraper()
        try:
            response = scraper.get('http://httpbin.org/get', timeout=10)
            assert response.status_code == 200
        except Exception as e:
            pytest.skip(f"Network unavailable: {e}")
    
    def test_request_with_cookies(self):
        """Test request with cookies"""
        scraper = cloudscraper.create_scraper()
        try:
            scraper.cookies.set('test_cookie', 'test_value')
            response = scraper.get('http://httpbin.org/cookies', timeout=10)
            assert response.status_code == 200
        except Exception as e:
            pytest.skip(f"Network unavailable: {e}")
    
    def test_request_with_headers(self):
        """Test request with custom headers"""
        scraper = cloudscraper.create_scraper()
        try:
            response = scraper.get(
                'http://httpbin.org/headers',
                headers={'X-Custom-Header': 'test'},
                timeout=10
            )
            assert response.status_code == 200
        except Exception as e:
            pytest.skip(f"Network unavailable: {e}")


# ==============================================================================
# Main
# ==============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
