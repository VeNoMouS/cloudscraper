#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Example script demonstrating how to handle Cloudflare Turnstile challenges
with cloudscraper.

Turnstile is Cloudflare's CAPTCHA alternative that provides a more
user-friendly verification experience.

This example shows how to:
1. Configure cloudscraper with a CAPTCHA provider
2. Access a site protected by Turnstile
3. Handle the challenge automatically

Usage:
    python turnstile_example.py <url> <captcha_provider> <api_key>

Example:
    python turnstile_example.py https://example.com 2captcha your_api_key
"""

import cloudscraper
import argparse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Cloudflare Turnstile Example')
    parser.add_argument('url', help='URL to access')
    parser.add_argument('--provider', help='Captcha provider (e.g., 2captcha, anticaptcha)')
    parser.add_argument('--api-key', help='API key for the captcha provider')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--proxy', help='Proxy to use (e.g., http://user:pass@host:port)')
    parser.add_argument('--test-mode', action='store_true', help='Run in test mode without a captcha provider')

    args = parser.parse_args()

    # Configure captcha provider
    captcha_config = {}
    if args.provider and args.api_key:
        captcha_config = {
            'provider': args.provider,
            'api_key': args.api_key
        }
    elif not args.test_mode:
        logger.warning("No captcha provider configured. Running in test mode.")
        logger.warning("Turnstile challenges will not be solved automatically.")
        args.test_mode = True

    # Configure proxy if specified
    proxies = None
    if args.proxy:
        proxies = {
            'http': args.proxy,
            'https': args.proxy
        }

    logger.info("Creating cloudscraper instance with Turnstile support...")

    # Create scraper with Turnstile support
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
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Cookies: {scraper.cookies.get_dict()}")

            # Print the first 500 characters of the response
            content_preview = response.text[:500] + "..." if len(response.text) > 500 else response.text
            logger.info(f"Response content preview: {content_preview}")
        else:
            logger.error(f"Failed to access URL. Status code: {response.status_code}")
            logger.error(f"Response content: {response.text[:1000]}")

    except Exception as e:
        logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
