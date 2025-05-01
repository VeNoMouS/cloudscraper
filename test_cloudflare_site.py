#!/usr/bin/env python
"""
Simple test script for cloudscraper25 with a Cloudflare-protected site
"""

import cloudscraper25
import argparse
import sys
import time
import json

def test_cloudflare_site(url, use_stealth=False, browser_type='chrome'):
    """
    Test accessing a Cloudflare-protected site
    
    Args:
        url (str): URL of the Cloudflare-protected site
        use_stealth (bool): Whether to use stealth mode
        browser_type (str): Browser type to emulate ('chrome' or 'firefox')
    """
    print(f"Testing cloudscraper25 version {cloudscraper25.__version__} on {url}")
    print(f"Browser: {browser_type}, Stealth mode: {'Enabled' if use_stealth else 'Disabled'}")
    
    # Configure scraper options
    options = {
        'browser': {
            'browser': browser_type,
            'platform': 'windows',
            'mobile': False
        }
    }
    
    if use_stealth:
        options['enable_stealth'] = True
        options['stealth_options'] = {
            'min_delay': 1.0,
            'max_delay': 3.0,
            'human_like_delays': True,
            'randomize_headers': True,
            'browser_quirks': True
        }
    
    try:
        # Create a scraper instance
        print("\nCreating scraper instance...")
        scraper = cloudscraper25.create_scraper(**options)
        
        # Make a request
        print(f"Making request to {url}...")
        start_time = time.time()
        response = scraper.get(url)
        end_time = time.time()
        
        # Print results
        print("\nRequest Results:")
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {end_time - start_time:.2f} seconds")
        print(f"Content Length: {len(response.text)} bytes")
        
        # Print cookies
        print("\nCookies:")
        for key, value in scraper.cookies.items():
            print(f"  {key}: {value}")
        
        # Print a sample of the response content
        print("\nResponse Content Sample:")
        print("-" * 50)
        print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
        print("-" * 50)
        
        # Check for Cloudflare cookies
        cf_cookies = [cookie for cookie in scraper.cookies.keys() if cookie.startswith('cf_') or cookie == '__cfduid']
        if cf_cookies:
            print("\nCloudflare cookies detected:")
            for cookie in cf_cookies:
                print(f"  {cookie}: {scraper.cookies.get(cookie)}")
        
        # Check if the response is successful
        if response.status_code == 200:
            print("\n✅ Test successful! Successfully bypassed Cloudflare protection.")
            return True
        else:
            print(f"\n❌ Test failed with status code {response.status_code}")
            return False
    
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Test cloudscraper25 with a Cloudflare-protected site')
    parser.add_argument('url', help='URL of the Cloudflare-protected site')
    parser.add_argument('-s', '--stealth', action='store_true', help='Enable stealth mode')
    parser.add_argument('-b', '--browser', choices=['chrome', 'firefox'], default='chrome', 
                        help='Browser to emulate (default: chrome)')
    
    args = parser.parse_args()
    
    success = test_cloudflare_site(args.url, args.stealth, args.browser)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
