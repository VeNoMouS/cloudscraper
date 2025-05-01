#!/usr/bin/env python
"""
Comprehensive test script for cloudscraper25 library
This script tests various features of the cloudscraper25 library
"""

import cloudscraper25
import time
import json
import sys
import argparse
from urllib.parse import urlparse

def test_basic_scraping(url, verbose=False):
    """Test basic scraping functionality"""
    print(f"\n[+] Testing basic scraping on {url}")
    
    try:
        # Create a scraper instance
        scraper = cloudscraper25.create_scraper()
        
        # Make a request
        start_time = time.time()
        response = scraper.get(url)
        end_time = time.time()
        
        # Print results
        print(f"  Status Code: {response.status_code}")
        print(f"  Response Time: {end_time - start_time:.2f} seconds")
        print(f"  Content Length: {len(response.text)} bytes")
        
        if verbose:
            print("\n  Headers:")
            for key, value in response.headers.items():
                print(f"    {key}: {value}")
            
            print("\n  Cookies:")
            for key, value in scraper.cookies.items():
                print(f"    {key}: {value}")
        
        # Check if the response is successful
        if response.status_code == 200:
            print("  [✓] Basic scraping test passed!")
            return True
        else:
            print(f"  [✗] Basic scraping test failed with status code {response.status_code}")
            return False
    
    except Exception as e:
        print(f"  [✗] Basic scraping test failed with error: {str(e)}")
        return False

def test_browser_emulation(url, browser_type='chrome', verbose=False):
    """Test browser emulation with different browser configurations"""
    print(f"\n[+] Testing browser emulation ({browser_type}) on {url}")
    
    try:
        # Create a scraper with specific browser configuration
        scraper = cloudscraper25.create_scraper(
            browser={
                'browser': browser_type,
                'platform': 'windows',
                'mobile': False
            }
        )
        
        # Make a request
        start_time = time.time()
        response = scraper.get(url)
        end_time = time.time()
        
        # Print results
        print(f"  Status Code: {response.status_code}")
        print(f"  Response Time: {end_time - start_time:.2f} seconds")
        print(f"  User-Agent: {scraper.headers['User-Agent']}")
        
        if verbose:
            print("\n  Headers:")
            for key, value in response.headers.items():
                print(f"    {key}: {value}")
        
        # Check if the response is successful
        if response.status_code == 200:
            print(f"  [✓] Browser emulation ({browser_type}) test passed!")
            return True
        else:
            print(f"  [✗] Browser emulation ({browser_type}) test failed with status code {response.status_code}")
            return False
    
    except Exception as e:
        print(f"  [✗] Browser emulation ({browser_type}) test failed with error: {str(e)}")
        return False

def test_stealth_mode(url, verbose=False):
    """Test stealth mode functionality"""
    print(f"\n[+] Testing stealth mode on {url}")
    
    try:
        # Create a scraper with stealth mode enabled
        scraper = cloudscraper25.create_scraper(
            enable_stealth=True,
            stealth_options={
                'min_delay': 1.0,
                'max_delay': 3.0,
                'human_like_delays': True,
                'randomize_headers': True,
                'browser_quirks': True
            }
        )
        
        # Make a request
        start_time = time.time()
        response = scraper.get(url)
        end_time = time.time()
        
        # Print results
        print(f"  Status Code: {response.status_code}")
        print(f"  Response Time: {end_time - start_time:.2f} seconds")
        
        if verbose:
            print("\n  Headers:")
            for key, value in scraper.headers.items():
                print(f"    {key}: {value}")
        
        # Check if the response is successful
        if response.status_code == 200:
            print("  [✓] Stealth mode test passed!")
            return True
        else:
            print(f"  [✗] Stealth mode test failed with status code {response.status_code}")
            return False
    
    except Exception as e:
        print(f"  [✗] Stealth mode test failed with error: {str(e)}")
        return False

def test_get_tokens(url, verbose=False):
    """Test getting Cloudflare tokens"""
    print(f"\n[+] Testing get_tokens on {url}")
    
    try:
        # Get tokens
        start_time = time.time()
        tokens, user_agent = cloudscraper25.get_tokens(url)
        end_time = time.time()
        
        # Print results
        print(f"  Time to get tokens: {end_time - start_time:.2f} seconds")
        print(f"  User-Agent: {user_agent}")
        
        if verbose:
            print("\n  Tokens:")
            for key, value in tokens.items():
                print(f"    {key}: {value}")
        
        # Check if tokens were obtained
        if tokens and len(tokens) > 0:
            print("  [✓] get_tokens test passed!")
            return True
        else:
            print("  [✗] get_tokens test failed - no tokens obtained")
            return False
    
    except Exception as e:
        print(f"  [✗] get_tokens test failed with error: {str(e)}")
        return False

def test_get_cookie_string(url, verbose=False):
    """Test getting cookie string"""
    print(f"\n[+] Testing get_cookie_string on {url}")
    
    try:
        # Get cookie string
        start_time = time.time()
        cookie_string, user_agent = cloudscraper25.get_cookie_string(url)
        end_time = time.time()
        
        # Print results
        print(f"  Time to get cookie string: {end_time - start_time:.2f} seconds")
        print(f"  User-Agent: {user_agent}")
        
        if verbose:
            print(f"  Cookie String: {cookie_string}")
        
        # Check if cookie string was obtained
        if cookie_string and len(cookie_string) > 0:
            print("  [✓] get_cookie_string test passed!")
            return True
        else:
            print("  [✗] get_cookie_string test failed - no cookie string obtained")
            return False
    
    except Exception as e:
        print(f"  [✗] get_cookie_string test failed with error: {str(e)}")
        return False

def test_different_interpreters(url, verbose=False):
    """Test different JavaScript interpreters"""
    interpreters = ['js2py', 'native']  # Add 'nodejs', 'chakracore', 'v8' if installed
    results = {}
    
    for interpreter in interpreters:
        print(f"\n[+] Testing {interpreter} interpreter on {url}")
        
        try:
            # Create a scraper with specific interpreter
            scraper = cloudscraper25.create_scraper(interpreter=interpreter)
            
            # Make a request
            start_time = time.time()
            response = scraper.get(url)
            end_time = time.time()
            
            # Print results
            print(f"  Status Code: {response.status_code}")
            print(f"  Response Time: {end_time - start_time:.2f} seconds")
            
            # Check if the response is successful
            if response.status_code == 200:
                print(f"  [✓] {interpreter} interpreter test passed!")
                results[interpreter] = True
            else:
                print(f"  [✗] {interpreter} interpreter test failed with status code {response.status_code}")
                results[interpreter] = False
        
        except Exception as e:
            print(f"  [✗] {interpreter} interpreter test failed with error: {str(e)}")
            results[interpreter] = False
    
    # Print summary
    print("\n[+] Interpreter Test Summary:")
    for interpreter, result in results.items():
        status = "✓" if result else "✗"
        print(f"  [{status}] {interpreter}")
    
    return all(results.values())

def run_all_tests(url, verbose=False):
    """Run all tests and return a summary"""
    results = {}
    
    # Run tests
    results["Basic Scraping"] = test_basic_scraping(url, verbose)
    results["Chrome Emulation"] = test_browser_emulation(url, 'chrome', verbose)
    results["Firefox Emulation"] = test_browser_emulation(url, 'firefox', verbose)
    results["Stealth Mode"] = test_stealth_mode(url, verbose)
    results["Get Tokens"] = test_get_tokens(url, verbose)
    results["Get Cookie String"] = test_get_cookie_string(url, verbose)
    
    # Only run interpreter tests if verbose mode is enabled
    if verbose:
        results["Different Interpreters"] = test_different_interpreters(url, verbose)
    
    # Print summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    # Calculate overall result
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print("-"*50)
    print(f"Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("="*50)
    
    return all(results.values())

def main():
    parser = argparse.ArgumentParser(description='Test cloudscraper25 library')
    parser.add_argument('url', help='URL to test (should be protected by Cloudflare)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('-t', '--test', choices=['basic', 'browser', 'stealth', 'tokens', 'cookie', 'interpreters', 'all'], 
                        default='all', help='Specific test to run')
    
    args = parser.parse_args()
    
    # Validate URL
    try:
        result = urlparse(args.url)
        if not all([result.scheme, result.netloc]):
            raise ValueError("Invalid URL")
    except Exception:
        print("Error: Please provide a valid URL (e.g., https://example.com)")
        return 1
    
    # Print library version
    print(f"cloudscraper25 version: {cloudscraper25.__version__}")
    
    # Run selected test
    if args.test == 'basic':
        test_basic_scraping(args.url, args.verbose)
    elif args.test == 'browser':
        test_browser_emulation(args.url, 'chrome', args.verbose)
        test_browser_emulation(args.url, 'firefox', args.verbose)
    elif args.test == 'stealth':
        test_stealth_mode(args.url, args.verbose)
    elif args.test == 'tokens':
        test_get_tokens(args.url, args.verbose)
    elif args.test == 'cookie':
        test_get_cookie_string(args.url, args.verbose)
    elif args.test == 'interpreters':
        test_different_interpreters(args.url, args.verbose)
    else:  # 'all'
        run_all_tests(args.url, args.verbose)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
