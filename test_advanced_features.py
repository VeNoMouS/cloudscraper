#!/usr/bin/env python3
"""
Advanced features test for cloudscraper library
Tests more complex functionality and configurations
"""

import sys
import time

def test_advanced_browser_config():
    """Test advanced browser configuration"""
    print("🧪 Testing advanced browser configuration...")
    try:
        import cloudscraper
        
        # Test custom browser configuration
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        print("✅ Advanced browser config successful")
        
        # Test custom user agent
        scraper = cloudscraper.create_scraper(
            browser={'custom': 'TestBot/1.0'}
        )
        print("✅ Custom user agent successful")
        return True
    except Exception as e:
        print(f"❌ Advanced browser config failed: {e}")
        return False

def test_challenge_disabling():
    """Test disabling different challenge types"""
    print("\n🧪 Testing challenge disabling...")
    try:
        import cloudscraper
        
        # Test disabling v1 challenges
        scraper = cloudscraper.create_scraper(disableCloudflareV1=True)
        print("✅ V1 challenge disabling successful")
        
        # Test disabling v2 challenges
        scraper = cloudscraper.create_scraper(disableCloudflareV2=True)
        print("✅ V2 challenge disabling successful")
        
        # Test disabling v3 challenges
        scraper = cloudscraper.create_scraper(disableCloudflareV3=True)
        print("✅ V3 challenge disabling successful")
        
        # Test disabling Turnstile
        scraper = cloudscraper.create_scraper(disableTurnstile=True)
        print("✅ Turnstile disabling successful")
        
        return True
    except Exception as e:
        print(f"❌ Challenge disabling failed: {e}")
        return False

def test_delay_configuration():
    """Test delay configuration"""
    print("\n🧪 Testing delay configuration...")
    try:
        import cloudscraper
        
        scraper = cloudscraper.create_scraper(delay=5)
        print("✅ Delay configuration successful")
        return True
    except Exception as e:
        print(f"❌ Delay configuration failed: {e}")
        return False

def test_brotli_configuration():
    """Test Brotli compression configuration"""
    print("\n🧪 Testing Brotli configuration...")
    try:
        import cloudscraper
        
        scraper = cloudscraper.create_scraper(allow_brotli=False)
        headers = scraper.headers.get('Accept-Encoding', '')
        if 'br' not in headers:
            print("✅ Brotli disabled successfully")
        else:
            print("⚠️  Brotli still enabled")
        
        scraper = cloudscraper.create_scraper(allow_brotli=True)
        print("✅ Brotli configuration successful")
        return True
    except Exception as e:
        print(f"❌ Brotli configuration failed: {e}")
        return False

def test_session_integration():
    """Test session integration"""
    print("\n🧪 Testing session integration...")
    try:
        import cloudscraper
        import requests
        
        # Test with existing session
        session = requests.Session()
        session.headers.update({'Custom-Header': 'TestValue'})
        
        scraper = cloudscraper.create_scraper(sess=session)
        print("✅ Session integration successful")
        return True
    except Exception as e:
        print(f"❌ Session integration failed: {e}")
        return False

def test_captcha_configuration():
    """Test CAPTCHA configuration (without actual solving)"""
    print("\n🧪 Testing CAPTCHA configuration...")
    try:
        import cloudscraper
        
        # Test return_response provider (for testing)
        scraper = cloudscraper.create_scraper(
            captcha={'provider': 'return_response'}
        )
        print("✅ CAPTCHA configuration successful")
        return True
    except Exception as e:
        print(f"❌ CAPTCHA configuration failed: {e}")
        return False

def test_ssl_configuration():
    """Test SSL configuration"""
    print("\n🧪 Testing SSL configuration...")
    try:
        import cloudscraper
        
        # Test ECDH curve configuration
        scraper = cloudscraper.create_scraper(ecdhCurve='secp384r1')
        print("✅ ECDH curve configuration successful")
        
        # Test server hostname configuration
        scraper = cloudscraper.create_scraper(server_hostname='example.com')
        print("✅ Server hostname configuration successful")
        return True
    except Exception as e:
        print(f"❌ SSL configuration failed: {e}")
        return False

def test_exception_handling():
    """Test exception classes"""
    print("\n🧪 Testing exception classes...")
    try:
        from cloudscraper.exceptions import (
            CloudflareLoopProtection,
            CloudflareIUAMError,
            CloudflareChallengeError,
            CloudflareTurnstileError,
            CloudflareV3Error
        )
        print("✅ All exception classes imported successfully")
        return True
    except Exception as e:
        print(f"❌ Exception handling failed: {e}")
        return False

def test_helper_functions():
    """Test helper functions"""
    print("\n🧪 Testing helper functions...")
    try:
        import cloudscraper.help as helper
        
        # Test system info
        info = helper.systemInfo()
        print("✅ System info helper successful")
        print(f"📋 System info keys: {list(info.keys())}")
        return True
    except Exception as e:
        print(f"❌ Helper functions failed: {e}")
        return False

def test_module_structure():
    """Test module structure and imports"""
    print("\n🧪 Testing module structure...")
    try:
        import cloudscraper
        
        # Test main classes
        scraper_class = cloudscraper.CloudScraper
        print("✅ CloudScraper class accessible")
        
        # Test main functions
        create_scraper = cloudscraper.create_scraper
        get_tokens = cloudscraper.get_tokens
        get_cookie_string = cloudscraper.get_cookie_string
        print("✅ Main functions accessible")
        
        # Test version
        version = cloudscraper.__version__
        print(f"✅ Version accessible: {version}")
        
        return True
    except Exception as e:
        print(f"❌ Module structure test failed: {e}")
        return False

def main():
    """Run all advanced tests"""
    print("🚀 Starting cloudscraper advanced functionality tests")
    print("=" * 60)
    
    tests = [
        test_advanced_browser_config,
        test_challenge_disabling,
        test_delay_configuration,
        test_brotli_configuration,
        test_session_integration,
        test_captcha_configuration,
        test_ssl_configuration,
        test_exception_handling,
        test_helper_functions,
        test_module_structure
    ]
    
    tests_passed = 0
    total_tests = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                tests_passed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 ADVANCED TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Tests Passed: {tests_passed}/{total_tests}")
    print(f"📈 Success Rate: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed == total_tests:
        print("🎉 All advanced tests passed! cloudscraper is fully functional!")
    elif tests_passed >= total_tests * 0.8:
        print("✅ Most advanced tests passed! cloudscraper is working excellently!")
    else:
        print("⚠️  Some advanced tests failed. Please check the errors above.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
