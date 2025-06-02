#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cloudscraper
import argparse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Test Cloudflare Turnstile handling')
    parser.add_argument('url', help='URL to test')
    parser.add_argument('--captcha-provider', help='Captcha provider to use (e.g., 2captcha, anticaptcha)')
    parser.add_argument('--api-key', help='API key for the captcha provider')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--proxy', help='Proxy to use (e.g., http://user:pass@host:port)')

    args = parser.parse_args()

    # Configure captcha provider if specified
    captcha_config = {}
    if args.captcha_provider and args.api_key:
        captcha_config = {
            'provider': args.captcha_provider,
            'api_key': args.api_key
        }

    # Configure proxy if specified
    proxies = None
    if args.proxy:
        proxies = {
            'http': args.proxy,
            'https': args.proxy
        }

    # Create scraper with appropriate configuration
    scraper = cloudscraper.create_scraper(
        debug=args.debug,
        captcha=captcha_config
    )

    # Set proxies if specified
    if proxies:
        scraper.proxies = proxies

    try:
        # Attempt to access the URL
        logger.info(f"Accessing URL: {args.url}")
        response = scraper.get(args.url)

        # Check if successful
        if response.status_code == 200:
            logger.info("Successfully accessed the URL")
            logger.info(f"Response headers: {response.headers}")
            logger.info(f"Cookies: {scraper.cookies.get_dict()}")

            # Print the first 500 characters of the response
            content_preview = response.text[:500] + "..." if len(response.text) > 500 else response.text
            logger.info(f"Response content preview: {content_preview}")
        else:
            logger.error(f"Failed to access URL. Status code: {response.status_code}")
            logger.error(f"Response content: {response.text}")

    except Exception as e:
        logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
