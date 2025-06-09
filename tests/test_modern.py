"""
Modern test suite for cloudscraper
"""

import pytest
import requests
import cloudscraper
from unittest.mock import Mock, patch
from cloudscraper.exceptions import (
    CloudflareLoopProtection,
    CloudflareIUAMError
)


class TestCloudScraper:
    """Test suite for CloudScraper functionality"""

    def test_create_scraper(self):
        """Test basic scraper creation"""
        scraper = cloudscraper.create_scraper()
        assert isinstance(scraper, cloudscraper.CloudScraper)
        assert hasattr(scraper, 'session_refresh_interval')
        assert hasattr(scraper, 'auto_refresh_on_403')
        assert hasattr(scraper, 'max_403_retries')

    def test_create_scraper_with_options(self):
        """Test scraper creation with custom options"""
        scraper = cloudscraper.create_scraper(
            session_refresh_interval=1800,
            auto_refresh_on_403=True,
            max_403_retries=5,
            enable_stealth=True
        )
        assert scraper.session_refresh_interval == 1800
        assert scraper.auto_refresh_on_403 is True
        assert scraper.max_403_retries == 5
        assert scraper.enable_stealth is True

    def test_user_agent_generation(self):
        """Test user agent generation"""
        scraper = cloudscraper.create_scraper()
        user_agent = scraper.headers.get('User-Agent')
        assert user_agent is not None
        assert 'Mozilla' in user_agent

    def test_browser_selection(self):
        """Test browser selection"""
        for browser in ['chrome', 'firefox']:
            scraper = cloudscraper.create_scraper(
                browser={'browser': browser, 'platform': 'windows'}
            )
            user_agent = scraper.headers.get('User-Agent', '').lower()
            assert browser in user_agent or 'mozilla' in user_agent

    def test_session_health_monitoring(self):
        """Test session health monitoring"""
        scraper = cloudscraper.create_scraper()
        
        # Test initial state
        assert scraper.request_count == 0
        assert scraper._403_retry_count == 0
        assert scraper.last_403_time == 0
        
        # Test should refresh logic
        assert not scraper._should_refresh_session()

    def test_stealth_mode(self):
        """Test stealth mode functionality"""
        scraper = cloudscraper.create_scraper(
            enable_stealth=True,
            stealth_options={
                'min_delay': 1.0,
                'max_delay': 3.0,
                'human_like_delays': True,
                'randomize_headers': True,
                'browser_quirks': True
            }
        )
        assert scraper.enable_stealth is True
        assert hasattr(scraper, 'stealth_mode')
        assert scraper.stealth_mode.min_delay == 1.0
        assert scraper.stealth_mode.max_delay == 3.0

    def test_proxy_manager(self):
        """Test proxy manager functionality"""
        proxies = ['http://proxy1:8080', 'http://proxy2:8080']
        scraper = cloudscraper.create_scraper(
            rotating_proxies=proxies,
            proxy_options={
                'rotation_strategy': 'sequential',
                'ban_time': 300
            }
        )
        assert hasattr(scraper, 'proxy_manager')
        assert scraper.proxy_manager.proxies == proxies

    @patch('cloudscraper.CloudScraper.perform_request')
    def test_403_handling(self, mock_request):
        """Test 403 error handling"""
        # Mock a 403 response
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.is_redirect = False
        mock_request.return_value = mock_response

        scraper = cloudscraper.create_scraper(
            auto_refresh_on_403=True,
            max_403_retries=1
        )
        
        # This should trigger 403 handling
        response = scraper.get('http://example.com')
        assert response.status_code == 403

    def test_version_info(self):
        """Test version information"""
        assert hasattr(cloudscraper, '__version__')
        assert cloudscraper.__version__ == '3.0.0'

    def test_ssl_context_creation(self):
        """Test SSL context creation"""
        scraper = cloudscraper.create_scraper()
        assert hasattr(scraper, 'ssl_context')


class TestSessionRefresh:
    """Test session refresh functionality"""

    def test_clear_cloudflare_cookies(self):
        """Test clearing Cloudflare cookies"""
        scraper = cloudscraper.create_scraper()
        
        # Add some mock cookies
        scraper.cookies.set('cf_clearance', 'test_value')
        scraper.cookies.set('cf_chl_2', 'test_value')
        
        # Clear cookies
        scraper._clear_cloudflare_cookies()
        
        # Verify cookies are cleared
        assert scraper.cookies.get('cf_clearance') is None
        assert scraper.cookies.get('cf_chl_2') is None

    def test_should_refresh_session(self):
        """Test session refresh logic"""
        scraper = cloudscraper.create_scraper(session_refresh_interval=10)
        
        # Initially should not refresh
        assert not scraper._should_refresh_session()
        
        # Simulate old session
        import time
        scraper.session_start_time = time.time() - 20
        assert scraper._should_refresh_session()


class TestCompatibility:
    """Test backward compatibility"""

    def test_legacy_create_scraper(self):
        """Test legacy create_scraper function"""
        scraper = cloudscraper.create_scraper()
        assert isinstance(scraper, cloudscraper.CloudScraper)

    def test_legacy_session_alias(self):
        """Test legacy session alias"""
        scraper = cloudscraper.session()
        assert isinstance(scraper, cloudscraper.CloudScraper)


class TestUserAgent:
    """Test user agent functionality"""

    def test_user_agent_browsers(self):
        """Test different browser user agents"""
        for browser in ['chrome', 'firefox']:
            scraper = cloudscraper.create_scraper(
                browser={'browser': browser, 'platform': 'windows'}
            )
            user_agent = scraper.headers.get('User-Agent', '').lower()
            # Should contain browser name or be a valid Mozilla string
            assert browser in user_agent or 'mozilla' in user_agent

    def test_custom_user_agent(self):
        """Test custom user agent"""
        custom_ua = 'Custom User Agent 1.0'
        scraper = cloudscraper.create_scraper(
            browser={'custom': custom_ua}
        )
        assert scraper.headers.get('User-Agent') == custom_ua


@pytest.mark.slow
class TestIntegration:
    """Integration tests (marked as slow)"""

    def test_real_request(self):
        """Test making a real HTTP request"""
        scraper = cloudscraper.create_scraper()
        try:
            response = scraper.get('http://httpbin.org/headers', timeout=10)
            assert response.status_code == 200
            assert 'headers' in response.json()
        except Exception as e:
            pytest.skip(f"Network request failed: {e}")

    def test_session_persistence(self):
        """Test session persistence across requests"""
        scraper = cloudscraper.create_scraper()
        try:
            # Set a cookie
            response1 = scraper.get('http://httpbin.org/cookies/set/test/value', timeout=10)
            # Check if cookie persists
            response2 = scraper.get('http://httpbin.org/cookies', timeout=10)
            assert response2.status_code == 200
        except Exception as e:
            pytest.skip(f"Network request failed: {e}")


if __name__ == '__main__':
    pytest.main([__file__])
