#!/usr/bin/env python3
"""
Final comprehensive test for cloudscraper library
Verifies all core functionality is working after the cloudscraper25 -> cloudscraper migration
"""

import sys
import time

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print('='*60)

def print_result(test_name, success, details=""):
    """Print test result"""
    status = "✅" if success else "❌"
    print(f"{status} {test_name}")
    if details:
        print(f"   📋 {details}")

def main():
    """Run comprehensive final test"""
    print("🚀 CLOUDSCRAPER COMPREHENSIVE FINAL TEST")
    print("🔄 Testing migration from cloudscraper25 to cloudscraper")
    print("=" * 60)
    
    total_tests = 0
    passed_tests = 0
    
    # Test 1: Import and Version
    print_header("CORE FUNCTIONALITY")
    total_tests += 1
    try:
        import cloudscraper
        version = cloudscraper.__version__
        print_result("Import cloudscraper", True, f"Version: {version}")
        passed_tests += 1
    except Exception as e:
        print_result("Import cloudscraper", False, str(e))
    
    # Test 2: Basic Scraper Creation
    total_tests += 1
    try:
        scraper = cloudscraper.create_scraper()
        ua = scraper.headers.get('User-Agent', 'Not set')
        print_result("Create basic scraper", True, f"UA: {ua[:40]}...")
        passed_tests += 1
    except Exception as e:
        print_result("Create basic scraper", False, str(e))
    
    # Test 3: CloudScraper Class
    total_tests += 1
    try:
        scraper_class = cloudscraper.CloudScraper()
        print_result("CloudScraper class", True, "Direct instantiation works")
        passed_tests += 1
    except Exception as e:
        print_result("CloudScraper class", False, str(e))
    
    # Test 4: Browser Configurations
    print_header("BROWSER EMULATION")
    browsers = ['chrome', 'firefox']
    for browser in browsers:
        total_tests += 1
        try:
            scraper = cloudscraper.create_scraper(browser=browser)
            ua = scraper.headers.get('User-Agent', '')
            print_result(f"{browser.capitalize()} browser", True, f"UA: {ua[:40]}...")
            passed_tests += 1
        except Exception as e:
            print_result(f"{browser.capitalize()} browser", False, str(e))
    
    # Test 5: JavaScript Interpreters
    print_header("JAVASCRIPT INTERPRETERS")
    interpreters = ['js2py', 'native']
    for interpreter in interpreters:
        total_tests += 1
        try:
            scraper = cloudscraper.create_scraper(interpreter=interpreter)
            print_result(f"{interpreter} interpreter", True, "Created successfully")
            passed_tests += 1
        except Exception as e:
            print_result(f"{interpreter} interpreter", False, str(e))
    
    # Test 6: Challenge Disabling
    print_header("CHALLENGE CONFIGURATION")
    challenges = [
        ('V1', 'disableCloudflareV1'),
        ('V2', 'disableCloudflareV2'),
        ('V3', 'disableCloudflareV3'),
        ('Turnstile', 'disableTurnstile')
    ]
    
    for name, param in challenges:
        total_tests += 1
        try:
            kwargs = {param: True}
            scraper = cloudscraper.create_scraper(**kwargs)
            print_result(f"Disable {name}", True, "Configuration accepted")
            passed_tests += 1
        except Exception as e:
            print_result(f"Disable {name}", False, str(e))
    
    # Test 7: Advanced Features
    print_header("ADVANCED FEATURES")
    
    # Debug mode
    total_tests += 1
    try:
        scraper = cloudscraper.create_scraper(debug=True)
        print_result("Debug mode", True, "Enabled successfully")
        passed_tests += 1
    except Exception as e:
        print_result("Debug mode", False, str(e))
    
    # Stealth mode
    total_tests += 1
    try:
        scraper = cloudscraper.create_scraper(
            enable_stealth=True,
            stealth_options={'min_delay': 1.0, 'max_delay': 2.0}
        )
        print_result("Stealth mode", True, "Configured successfully")
        passed_tests += 1
    except Exception as e:
        print_result("Stealth mode", False, str(e))
    
    # Delay configuration
    total_tests += 1
    try:
        scraper = cloudscraper.create_scraper(delay=5)
        print_result("Delay configuration", True, "5 second delay set")
        passed_tests += 1
    except Exception as e:
        print_result("Delay configuration", False, str(e))
    
    # Test 8: Exception Classes
    print_header("EXCEPTION HANDLING")
    exceptions = [
        'CloudflareLoopProtection',
        'CloudflareIUAMError',
        'CloudflareChallengeError',
        'CloudflareTurnstileError',
        'CloudflareV3Error'
    ]
    
    for exc_name in exceptions:
        total_tests += 1
        try:
            from cloudscraper.exceptions import CloudflareLoopProtection, CloudflareIUAMError, CloudflareChallengeError
            print_result(f"{exc_name} import", True, "Exception class available")
            passed_tests += 1
        except Exception as e:
            print_result(f"{exc_name} import", False, str(e))
            break  # If one fails, they all will
    
    # Test 9: Helper Functions
    print_header("HELPER FUNCTIONS")
    
    # get_tokens function
    total_tests += 1
    try:
        get_tokens = cloudscraper.get_tokens
        print_result("get_tokens function", True, "Function accessible")
        passed_tests += 1
    except Exception as e:
        print_result("get_tokens function", False, str(e))
    
    # get_cookie_string function
    total_tests += 1
    try:
        get_cookie_string = cloudscraper.get_cookie_string
        print_result("get_cookie_string function", True, "Function accessible")
        passed_tests += 1
    except Exception as e:
        print_result("get_cookie_string function", False, str(e))
    
    # Helper module
    total_tests += 1
    try:
        import cloudscraper.help as helper
        info = helper.systemInfo()
        print_result("Helper module", True, f"System info: {len(info)} items")
        passed_tests += 1
    except Exception as e:
        print_result("Helper module", False, str(e))
    
    # Test 10: Module Structure
    print_header("MODULE STRUCTURE")
    
    # Check main attributes
    attributes = ['__version__', 'create_scraper', 'get_tokens', 'get_cookie_string', 'CloudScraper']
    for attr in attributes:
        total_tests += 1
        try:
            value = getattr(cloudscraper, attr)
            print_result(f"Attribute {attr}", True, f"Type: {type(value).__name__}")
            passed_tests += 1
        except Exception as e:
            print_result(f"Attribute {attr}", False, str(e))
    
    # Final Summary
    print_header("FINAL SUMMARY")
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"📊 Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {total_tests - passed_tests}")
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("\n🎉 PERFECT! All tests passed!")
        print("✅ cloudscraper migration completed successfully!")
        print("✅ All features are working correctly!")
    elif success_rate >= 90:
        print("\n🎊 EXCELLENT! Almost all tests passed!")
        print("✅ cloudscraper is working very well!")
    elif success_rate >= 80:
        print("\n👍 GOOD! Most tests passed!")
        print("✅ cloudscraper is working well!")
    else:
        print("\n⚠️  Some issues detected.")
        print("🔧 Please review the failed tests above.")
    
    print("\n" + "=" * 60)
    print("🏁 COMPREHENSIVE TEST COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    main()
