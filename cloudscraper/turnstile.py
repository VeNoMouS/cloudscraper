# Cloudflare Turnstile

import re
import time
import json
import logging
import random
from copy import deepcopy
from collections import OrderedDict

# ------------------------------------------------------------------------------- #

try:
    from urlparse import urlparse, urljoin
except ImportError:
    from urllib.parse import urlparse, urljoin

# ------------------------------------------------------------------------------- #

from .exceptions import (
    CloudflareIUAMError,
    CloudflareSolveError,
    CloudflareChallengeError,
    CloudflareCaptchaError,
    CloudflareCaptchaProvider,
    CloudflareTurnstileError
)

# ------------------------------------------------------------------------------- #

from .captcha import Captcha

# ------------------------------------------------------------------------------- #


class CloudflareTurnstile():

    def __init__(self, cloudscraper):
        self.cloudscraper = cloudscraper
        self.delay = self.cloudscraper.delay or random.uniform(1.0, 5.0)

    # ------------------------------------------------------------------------------- #
    # Check if the response contains a Cloudflare Turnstile challenge
    # ------------------------------------------------------------------------------- #

    @staticmethod
    def is_Turnstile_Challenge(resp):
        try:
            return (
                resp.headers.get('Server', '').startswith('cloudflare')
                and resp.status_code in [403, 429, 503]
                and (
                    re.search(
                        r'class="cf-turnstile"',
                        resp.text,
                        re.M | re.S
                    ) or
                    re.search(
                        r'src="https://challenges.cloudflare.com/turnstile/v0/api.js',
                        resp.text,
                        re.M | re.S
                    ) or
                    re.search(
                        r'data-sitekey="[0-9A-Za-z]{40}"',
                        resp.text,
                        re.M | re.S
                    )
                )
            )
        except AttributeError:
            pass

        return False

    # ------------------------------------------------------------------------------- #
    # Extract Turnstile challenge data from the page
    # ------------------------------------------------------------------------------- #

    def extract_turnstile_data(self, resp):
        try:
            # Extract the site key
            site_key = re.search(
                r'data-sitekey="([0-9A-Za-z]{40})"',
                resp.text
            )
            
            if not site_key:
                raise CloudflareTurnstileError("Could not find Turnstile site key")
                
            # Extract the form action URL
            form_action = re.search(
                r'<form .*?action="([^"]+)"',
                resp.text,
                re.DOTALL
            )
            
            if not form_action:
                # If no form action is found, use the current URL
                url_parsed = urlparse(resp.url)
                form_action_url = f"{url_parsed.scheme}://{url_parsed.netloc}{url_parsed.path}"
            else:
                form_action_url = form_action.group(1)
                
            return {
                'site_key': site_key.group(1),
                'form_action': form_action_url
            }
            
        except Exception as e:
            logging.error(f"Error extracting Cloudflare Turnstile data: {str(e)}")
            raise CloudflareTurnstileError(f"Error extracting Cloudflare Turnstile data: {str(e)}")

    # ------------------------------------------------------------------------------- #
    # Handle the Cloudflare Turnstile challenge
    # ------------------------------------------------------------------------------- #

    def handle_Turnstile_Challenge(self, resp, **kwargs):
        try:
            # Check if captcha provider is configured
            if (
                not self.cloudscraper.captcha
                or not isinstance(self.cloudscraper.captcha, dict)
                or not self.cloudscraper.captcha.get('provider')
            ):
                self.cloudscraper.simpleException(
                    CloudflareCaptchaProvider,
                    "Cloudflare Turnstile detected, but no captcha provider configured"
                )
                
            # Extract Turnstile data
            turnstile_info = self.extract_turnstile_data(resp)
            
            # Wait for the specified delay
            time.sleep(self.delay)
            
            # Solve the Turnstile challenge using the captcha provider
            turnstile_response = Captcha.dynamicImport(
                self.cloudscraper.captcha.get('provider').lower()
            ).solveCaptcha(
                'turnstile',
                resp.url,
                turnstile_info['site_key'],
                self.cloudscraper.captcha
            )
            
            # Prepare the payload
            payload = {
                'cf-turnstile-response': turnstile_response
            }
            
            # Add any additional form fields from the page
            for field in re.findall(r'<input[^>]*name="([^"]+)"[^>]*value="([^"]*)"', resp.text):
                if field[0] != 'cf-turnstile-response':
                    payload[field[0]] = field[1]
            
            # Prepare the request
            url_parsed = urlparse(resp.url)
            challenge_url = turnstile_info['form_action']
            if not challenge_url.startswith('http'):
                challenge_url = f"{url_parsed.scheme}://{url_parsed.netloc}{challenge_url}"
            
            # Add browser-like behavior
            cloudflare_kwargs = deepcopy(kwargs)
            cloudflare_kwargs['allow_redirects'] = False
            
            # Update headers to look more like a browser
            cloudflare_kwargs['headers'] = cloudflare_kwargs.get('headers', {})
            cloudflare_kwargs['headers'].update({
                'Origin': f'{url_parsed.scheme}://{url_parsed.netloc}',
                'Referer': resp.url,
                'Content-Type': 'application/x-www-form-urlencoded'
            })
            
            # Submit the challenge
            challenge_response = self.cloudscraper.request(
                'POST',
                challenge_url,
                data=payload,
                **cloudflare_kwargs
            )
            
            # Handle the response
            if challenge_response.status_code == 403:
                raise CloudflareSolveError("Failed to solve Cloudflare Turnstile challenge")
                
            return challenge_response
            
        except Exception as e:
            logging.error(f"Error handling Cloudflare Turnstile challenge: {str(e)}")
            raise CloudflareTurnstileError(f"Error handling Cloudflare Turnstile challenge: {str(e)}")
