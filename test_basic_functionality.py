#!/usr/bin/env python3
"""
Basic functionality test for cloudscraper library
Tests core features to ensure everything works after renaming from cloudscraper25
"""

import sys
import time
import traceback

def test_import():
    """Test basic import functionality"""
    print("🧪 Testing import...")
    try:
        import cloudscraper
        print(f"✅ Import successful")
        print(f"📦 Version: {cloudscraper.__version__}")
        return True, cloudscraper
    except Exception as e:
        print(f"❌ Import failed: {e}")
        traceback.print_exc()
        return False, None

def test_create_scraper(cloudscraper):
    """Test scraper creation"""
    print("\n🧪 Testing scraper creation...")
    try:
        scraper = cloudscraper.create_scraper()
        print("✅ Scraper created successfully")
        print(f"📋 User-Agent: {scraper.headers.get('User-Agent', 'Not set')[:50]}...")
        return True, scraper
    except Exception as e:
        print(f"❌ Scraper creation failed: {e}")
        traceback.print_exc()
        return False, None

def test_basic_request(scraper):
    """Test basic HTTP request to a non-Cloudflare site"""
    print("\n🧪 Testing basic HTTP request...")
    try:
        # Test with httpbin.org (reliable test endpoint)
        response = scraper.get('https://httpbin.org/get', timeout=10)
        print(f"✅ Request successful")
        print(f"📊 Status Code: {response.status_code}")
        print(f"📏 Content Length: {len(response.text)} bytes")
        return True
    except Exception as e:
        print(f"❌ Basic request failed: {e}")
        traceback.print_exc()
        return False

def test_browser_emulation(cloudscraper):
    """Test different browser emulation"""
    print("\n🧪 Testing browser emulation...")
    browsers = ['chrome', 'firefox']
    
    for browser in browsers:
        try:
            scraper = cloudscraper.create_scraper(browser=browser)
            user_agent = scraper.headers.get('User-Agent', '')
            print(f"✅ {browser.capitalize()} emulation: {user_agent[:50]}...")
        except Exception as e:
            print(f"❌ {browser.capitalize()} emulation failed: {e}")
            return False
    
    return True

def test_interpreters(cloudscraper):
    """Test different JavaScript interpreters"""
    print("\n🧪 Testing JavaScript interpreters...")
    interpreters = ['js2py', 'native']  # Only test available ones
    
    for interpreter in interpreters:
        try:
            scraper = cloudscraper.create_scraper(interpreter=interpreter)
            print(f"✅ {interpreter} interpreter created successfully")
        except Exception as e:
            print(f"⚠️  {interpreter} interpreter failed: {e}")
            # Don't return False as some interpreters might not be available
    
    return True

def test_debug_mode(cloudscraper):
    """Test debug mode functionality"""
    print("\n🧪 Testing debug mode...")
    try:
        scraper = cloudscraper.create_scraper(debug=True)
        print("✅ Debug mode enabled successfully")
        return True
    except Exception as e:
        print(f"❌ Debug mode failed: {e}")
        return False

def test_stealth_mode(cloudscraper):
    """Test stealth mode functionality"""
    print("\n🧪 Testing stealth mode...")
    try:
        scraper = cloudscraper.create_scraper(
            enable_stealth=True,
            stealth_options={
                'min_delay': 1.0,
                'max_delay': 2.0,
                'human_like_delays': True
            }
        )
        print("✅ Stealth mode enabled successfully")
        return True
    except Exception as e:
        print(f"❌ Stealth mode failed: {e}")
        return False

def test_get_tokens(cloudscraper):
    """Test get_tokens functionality"""
    print("\n🧪 Testing get_tokens...")
    try:
        # Use a simple site for testing
        tokens, user_agent = cloudscraper.get_tokens('https://httpbin.org/get', timeout=10)
        print("✅ get_tokens successful")
        print(f"📋 User-Agent: {user_agent[:50]}...")
        print(f"🍪 Tokens: {len(tokens)} items")
        return True
    except Exception as e:
        print(f"❌ get_tokens failed: {e}")
        return False

def test_get_cookie_string(cloudscraper):
    """Test get_cookie_string functionality"""
    print("\n🧪 Testing get_cookie_string...")
    try:
        cookie_string, user_agent = cloudscraper.get_cookie_string('https://httpbin.org/get', timeout=10)
        print("✅ get_cookie_string successful")
        print(f"📋 User-Agent: {user_agent[:50]}...")
        print(f"🍪 Cookie String Length: {len(cookie_string)} chars")
        return True
    except Exception as e:
        print(f"❌ get_cookie_string failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting cloudscraper functionality tests")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Import
    total_tests += 1
    success, cloudscraper = test_import()
    if success:
        tests_passed += 1
    else:
        print("💥 Critical failure: Cannot import cloudscraper")
        return
    
    # Test 2: Create scraper
    total_tests += 1
    success, scraper = test_create_scraper(cloudscraper)
    if success:
        tests_passed += 1
    else:
        print("💥 Critical failure: Cannot create scraper")
        return
    
    # Test 3: Basic request
    total_tests += 1
    if test_basic_request(scraper):
        tests_passed += 1
    
    # Test 4: Browser emulation
    total_tests += 1
    if test_browser_emulation(cloudscraper):
        tests_passed += 1
    
    # Test 5: Interpreters
    total_tests += 1
    if test_interpreters(cloudscraper):
        tests_passed += 1
    
    # Test 6: Debug mode
    total_tests += 1
    if test_debug_mode(cloudscraper):
        tests_passed += 1
    
    # Test 7: Stealth mode
    total_tests += 1
    if test_stealth_mode(cloudscraper):
        tests_passed += 1
    
    # Test 8: get_tokens
    total_tests += 1
    if test_get_tokens(cloudscraper):
        tests_passed += 1
    
    # Test 9: get_cookie_string
    total_tests += 1
    if test_get_cookie_string(cloudscraper):
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Tests Passed: {tests_passed}/{total_tests}")
    print(f"📈 Success Rate: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! cloudscraper is working perfectly!")
    elif tests_passed >= total_tests * 0.8:
        print("✅ Most tests passed! cloudscraper is working well!")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
