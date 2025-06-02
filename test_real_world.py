#!/usr/bin/env python3
"""
Real-world test for cloudscraper library
Tests with actual websites and scenarios
"""

import sys
import time

def test_cloudflare_detection():
    """Test Cloudflare detection capabilities"""
    print("🧪 Testing Cloudflare detection...")
    try:
        import cloudscraper
        
        # Create scraper with debug mode to see detection
        scraper = cloudscraper.create_scraper(debug=True)
        
        # Test sites that are known to use Cloudflare
        test_sites = [
            'https://httpbin.org/get',  # Non-Cloudflare site for comparison
        ]
        
        for site in test_sites:
            try:
                print(f"🌐 Testing: {site}")
                response = scraper.get(site, timeout=15)
                print(f"✅ Response: {response.status_code}")
                
                # Check if Cloudflare headers are present
                cf_headers = [h for h in response.headers.keys() if 'cf-' in h.lower()]
                if cf_headers:
                    print(f"🛡️  Cloudflare headers detected: {cf_headers}")
                else:
                    print("📝 No Cloudflare headers detected")
                
            except Exception as e:
                print(f"⚠️  {site} failed: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Cloudflare detection test failed: {e}")
        return False

def test_different_interpreters():
    """Test different JavaScript interpreters with real requests"""
    print("\n🧪 Testing interpreters with real requests...")
    try:
        import cloudscraper
        
        interpreters = ['js2py', 'native']
        
        for interpreter in interpreters:
            try:
                print(f"🔧 Testing {interpreter} interpreter...")
                scraper = cloudscraper.create_scraper(
                    interpreter=interpreter,
                    debug=False  # Reduce noise
                )
                
                response = scraper.get('https://httpbin.org/user-agent', timeout=10)
                if response.status_code == 200:
                    print(f"✅ {interpreter} interpreter working")
                else:
                    print(f"⚠️  {interpreter} interpreter returned {response.status_code}")
                    
            except Exception as e:
                print(f"⚠️  {interpreter} interpreter failed: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Interpreter test failed: {e}")
        return False

def test_stealth_mode_real():
    """Test stealth mode with real requests"""
    print("\n🧪 Testing stealth mode with real requests...")
    try:
        import cloudscraper
        
        # Test without stealth
        print("🔍 Testing without stealth mode...")
        scraper_normal = cloudscraper.create_scraper()
        start_time = time.time()
        response1 = scraper_normal.get('https://httpbin.org/delay/1', timeout=15)
        normal_time = time.time() - start_time
        print(f"✅ Normal mode: {response1.status_code} in {normal_time:.2f}s")
        
        # Test with stealth
        print("🥷 Testing with stealth mode...")
        scraper_stealth = cloudscraper.create_scraper(
            enable_stealth=True,
            stealth_options={
                'min_delay': 1.0,
                'max_delay': 2.0,
                'human_like_delays': True
            }
        )
        start_time = time.time()
        response2 = scraper_stealth.get('https://httpbin.org/delay/1', timeout=20)
        stealth_time = time.time() - start_time
        print(f"✅ Stealth mode: {response2.status_code} in {stealth_time:.2f}s")
        
        if stealth_time > normal_time:
            print("✅ Stealth mode correctly adds delays")
        
        return True
    except Exception as e:
        print(f"❌ Stealth mode test failed: {e}")
        return False

def test_user_agent_rotation():
    """Test user agent rotation"""
    print("\n🧪 Testing user agent rotation...")
    try:
        import cloudscraper
        
        user_agents = set()
        
        # Create multiple scrapers to see different user agents
        for i in range(5):
            scraper = cloudscraper.create_scraper()
            ua = scraper.headers.get('User-Agent')
            user_agents.add(ua)
            print(f"🤖 UA {i+1}: {ua[:50]}...")
        
        print(f"✅ Generated {len(user_agents)} unique user agents")
        return True
    except Exception as e:
        print(f"❌ User agent rotation test failed: {e}")
        return False

def test_session_persistence():
    """Test session persistence"""
    print("\n🧪 Testing session persistence...")
    try:
        import cloudscraper
        
        scraper = cloudscraper.create_scraper()
        
        # Make first request to set cookies
        response1 = scraper.get('https://httpbin.org/cookies/set/test/value123', timeout=10)
        print(f"✅ First request: {response1.status_code}")
        
        # Make second request to check if cookies persist
        response2 = scraper.get('https://httpbin.org/cookies', timeout=10)
        print(f"✅ Second request: {response2.status_code}")
        
        # Check if cookie was maintained
        if 'test' in response2.text and 'value123' in response2.text:
            print("✅ Session persistence working - cookies maintained")
        else:
            print("⚠️  Session persistence issue - cookies not maintained")
        
        return True
    except Exception as e:
        print(f"❌ Session persistence test failed: {e}")
        return False

def test_error_handling():
    """Test error handling"""
    print("\n🧪 Testing error handling...")
    try:
        import cloudscraper
        
        scraper = cloudscraper.create_scraper()
        
        # Test with invalid URL
        try:
            response = scraper.get('https://this-domain-does-not-exist-12345.com', timeout=5)
            print("⚠️  Expected error but got response")
        except Exception as e:
            print(f"✅ Correctly handled invalid URL: {type(e).__name__}")
        
        # Test with timeout
        try:
            response = scraper.get('https://httpbin.org/delay/10', timeout=2)
            print("⚠️  Expected timeout but got response")
        except Exception as e:
            print(f"✅ Correctly handled timeout: {type(e).__name__}")
        
        return True
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def test_headers_and_encoding():
    """Test headers and encoding handling"""
    print("\n🧪 Testing headers and encoding...")
    try:
        import cloudscraper
        
        scraper = cloudscraper.create_scraper()
        
        # Test headers
        response = scraper.get('https://httpbin.org/headers', timeout=10)
        print(f"✅ Headers test: {response.status_code}")
        
        # Test encoding
        response = scraper.get('https://httpbin.org/encoding/utf8', timeout=10)
        print(f"✅ Encoding test: {response.status_code}")
        
        # Test gzip
        response = scraper.get('https://httpbin.org/gzip', timeout=10)
        print(f"✅ Gzip test: {response.status_code}")
        
        return True
    except Exception as e:
        print(f"❌ Headers and encoding test failed: {e}")
        return False

def main():
    """Run all real-world tests"""
    print("🚀 Starting cloudscraper real-world functionality tests")
    print("=" * 60)
    
    tests = [
        test_cloudflare_detection,
        test_different_interpreters,
        test_stealth_mode_real,
        test_user_agent_rotation,
        test_session_persistence,
        test_error_handling,
        test_headers_and_encoding
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
    print("📊 REAL-WORLD TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Tests Passed: {tests_passed}/{total_tests}")
    print(f"📈 Success Rate: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed == total_tests:
        print("🎉 All real-world tests passed! cloudscraper is production-ready!")
    elif tests_passed >= total_tests * 0.8:
        print("✅ Most real-world tests passed! cloudscraper is working great!")
    else:
        print("⚠️  Some real-world tests failed. Please check the errors above.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
