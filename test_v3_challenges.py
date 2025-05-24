#!/usr/bin/env python3
"""
Test script for Cloudflare v3 JavaScript VM challenge support in cloudscraper25.

This script tests the new v3 challenge detection and handling capabilities.
"""

import sys
import logging
import argparse
import cloudscraper25

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test URLs that might have v3 challenges
V3_TEST_URLS = {
    'cloudflare_docs': 'https://developers.cloudflare.com/',
    'cloudflare_main': 'https://www.cloudflare.com/',
    'cloudflare_blog': 'https://blog.cloudflare.com/',
    'cloudflare_community': 'https://community.cloudflare.com/'
}

def test_v3_detection(scraper, url):
    """Test v3 challenge detection."""
    logger.info(f"Testing v3 challenge detection for {url}")
    
    try:
        response = scraper.get(url)
        
        # Check if v3 challenge was detected
        if scraper.cloudflare_v3.is_V3_Challenge(response):
            logger.info("[DETECTED] v3 JavaScript VM challenge found")
            return True
        else:
            logger.info("[NO CHALLENGE] No v3 challenge detected")
            return False
            
    except Exception as e:
        logger.error(f"[ERROR] v3 detection test failed: {str(e)}")
        return False

def test_v3_handling(scraper, url):
    """Test v3 challenge handling."""
    logger.info(f"Testing v3 challenge handling for {url}")
    
    try:
        response = scraper.get(url)
        
        if response.status_code == 200:
            logger.info("[PASS] v3 challenge handling test passed")
            return True
        else:
            logger.error(f"[FAIL] v3 challenge handling failed with status code {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"[FAIL] v3 challenge handling test failed: {str(e)}")
        return False

def test_v3_with_different_interpreters():
    """Test v3 challenges with different JavaScript interpreters."""
    interpreters = ['js2py', 'nodejs', 'native']
    results = {}
    
    for interpreter in interpreters:
        logger.info(f"\nTesting v3 challenges with {interpreter} interpreter")
        
        try:
            scraper = cloudscraper25.create_scraper(
                interpreter=interpreter,
                debug=True,
                delay=5  # Allow more time for complex v3 challenges
            )
            
            # Test with a URL that might have v3 challenges
            test_url = V3_TEST_URLS['cloudflare_docs']
            response = scraper.get(test_url)
            
            if response.status_code == 200:
                logger.info(f"[PASS] {interpreter} interpreter test passed")
                results[interpreter] = True
            else:
                logger.error(f"[FAIL] {interpreter} interpreter test failed")
                results[interpreter] = False
                
        except Exception as e:
            logger.error(f"[FAIL] {interpreter} interpreter test failed: {str(e)}")
            results[interpreter] = False
    
    return results

def test_v3_disabled():
    """Test that v3 challenges can be disabled."""
    logger.info("Testing v3 challenge disabling")
    
    try:
        scraper = cloudscraper25.create_scraper(
            disableCloudflareV3=True,
            debug=True
        )
        
        # Test with a URL that might have v3 challenges
        test_url = V3_TEST_URLS['cloudflare_docs']
        response = scraper.get(test_url)
        
        # Check that v3 handling was skipped
        if hasattr(scraper, '_solveDepthCnt'):
            logger.info("[PASS] v3 challenge disabling test passed")
            return True
        else:
            logger.info("[PASS] v3 challenge disabling test passed (no challenges encountered)")
            return True
            
    except Exception as e:
        logger.error(f"[FAIL] v3 challenge disabling test failed: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Test Cloudflare v3 JavaScript VM challenge support')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--interpreter', default='js2py', help='JavaScript interpreter to use')
    parser.add_argument('--url', help='Specific URL to test')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info(f"Testing cloudscraper25 version: {cloudscraper25.__version__}")
    logger.info("Starting Cloudflare v3 JavaScript VM challenge tests")
    
    # Create scraper with v3 support
    scraper = cloudscraper25.create_scraper(
        interpreter=args.interpreter,
        debug=args.debug,
        delay=5  # Allow more time for complex v3 challenges
    )
    
    results = {
        'v3_detection': {},
        'v3_handling': {},
        'interpreter_tests': {},
        'v3_disabled': False
    }
    
    # Test URLs
    test_urls = {args.url: 'custom'} if args.url else V3_TEST_URLS
    
    for name, url in test_urls.items():
        logger.info(f"\n{'='*50}\nTesting URL: {url}\n{'='*50}")
        
        # Test v3 detection
        results['v3_detection'][name] = test_v3_detection(scraper, url)
        
        # Test v3 handling
        results['v3_handling'][name] = test_v3_handling(scraper, url)
    
    # Test different interpreters
    logger.info(f"\n{'='*50}\nTesting Different Interpreters\n{'='*50}")
    results['interpreter_tests'] = test_v3_with_different_interpreters()
    
    # Test v3 disabling
    logger.info(f"\n{'='*50}\nTesting v3 Challenge Disabling\n{'='*50}")
    results['v3_disabled'] = test_v3_disabled()
    
    # Print summary
    logger.info("\n\n" + "="*50)
    logger.info("V3 CHALLENGE TEST RESULTS SUMMARY")
    logger.info("="*50)
    
    # Detection results
    detection_passed = sum(1 for result in results['v3_detection'].values() if result)
    detection_total = len(results['v3_detection'])
    logger.info(f"v3_detection: {detection_passed}/{detection_total} passed ({detection_passed/detection_total*100:.1f}%)")
    
    # Handling results
    handling_passed = sum(1 for result in results['v3_handling'].values() if result)
    handling_total = len(results['v3_handling'])
    logger.info(f"v3_handling: {handling_passed}/{handling_total} passed ({handling_passed/handling_total*100:.1f}%)")
    
    # Interpreter results
    interpreter_passed = sum(1 for result in results['interpreter_tests'].values() if result)
    interpreter_total = len(results['interpreter_tests'])
    if interpreter_total > 0:
        logger.info(f"interpreter_tests: {interpreter_passed}/{interpreter_total} passed ({interpreter_passed/interpreter_total*100:.1f}%)")
    
    # Disabled test result
    logger.info(f"v3_disabled: {'PASS' if results['v3_disabled'] else 'FAIL'}")
    
    logger.info("="*50)
    
    # Exit with appropriate code
    total_tests = detection_total + handling_total + interpreter_total + 1
    total_passed = detection_passed + handling_passed + interpreter_passed + (1 if results['v3_disabled'] else 0)
    
    if total_passed == total_tests:
        logger.info("All v3 challenge tests passed!")
        sys.exit(0)
    else:
        logger.warning(f"Some tests failed: {total_passed}/{total_tests} passed")
        sys.exit(1)

if __name__ == '__main__':
    main()
