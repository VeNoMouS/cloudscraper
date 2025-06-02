# Cloudflare V2

import re
import time
import json
import logging
import random
import base64
from copy import deepcopy
from collections import OrderedDict

# ------------------------------------------------------------------------------- #

try:
    from urlparse import urlparse, urljoin
except ImportError:
    from urllib.parse import urlparse, urljoin

# ------------------------------------------------------------------------------- #

from .exceptions import (
    CloudflareCode1020,
    CloudflareIUAMError,
    CloudflareSolveError,
    CloudflareChallengeError,
    CloudflareCaptchaError,
    CloudflareCaptchaProvider
)

# ------------------------------------------------------------------------------- #

from .captcha import Captcha
from .interpreters import JavaScriptInterpreter

# ------------------------------------------------------------------------------- #


class CloudflareV2():

    def __init__(self, cloudscraper):
        self.cloudscraper = cloudscraper
        self.delay = self.cloudscraper.delay or random.uniform(1.0, 5.0)

    # ------------------------------------------------------------------------------- #
    # Check if the response contains a Cloudflare v2 challenge
    # ------------------------------------------------------------------------------- #

    @staticmethod
    def is_V2_Challenge(resp):
        try:
            return (
                resp.headers.get('Server', '').startswith('cloudflare')
                and resp.status_code in [403, 429, 503]
                and re.search(
                    r'''cpo.src\s*=\s*['"]/cdn-cgi/challenge-platform/\S+orchestrate/jsch/v1''',
                    resp.text,
                    re.M | re.S
                )
            )
        except AttributeError:
            pass

        return False

    # ------------------------------------------------------------------------------- #
    # Check if the response contains a v2 hCaptcha Cloudflare challenge
    # ------------------------------------------------------------------------------- #

    @staticmethod
    def is_V2_Captcha_Challenge(resp):
        try:
            return (
                resp.headers.get('Server', '').startswith('cloudflare')
                and resp.status_code == 403
                and re.search(
                    r'''cpo.src\s*=\s*['"]/cdn-cgi/challenge-platform/\S+orchestrate/(captcha|managed)/v1''',
                    resp.text,
                    re.M | re.S
                )
            )
        except AttributeError:
            pass

        return False

    # ------------------------------------------------------------------------------- #
    # Extract challenge data from the page
    # ------------------------------------------------------------------------------- #

    def extract_challenge_data(self, resp):
        try:
            # Extract the challenge data from the JavaScript
            challenge_data = re.search(
                r'window\._cf_chl_opt=({.*?});',
                resp.text,
                re.DOTALL
            )
            
            if not challenge_data:
                raise CloudflareChallengeError("Could not find Cloudflare challenge data")
                
            challenge_data = json.loads(challenge_data.group(1))
            
            # Extract the form action URL
            form_action = re.search(
                r'<form .*?id="challenge-form" action="([^"]+)"',
                resp.text,
                re.DOTALL
            )
            
            if not form_action:
                raise CloudflareChallengeError("Could not find Cloudflare challenge form")
                
            return {
                'challenge_data': challenge_data,
                'form_action': form_action.group(1)
            }
            
        except Exception as e:
            logging.error(f"Error extracting Cloudflare challenge data: {str(e)}")
            raise CloudflareChallengeError(f"Error extracting Cloudflare challenge data: {str(e)}")

    # ------------------------------------------------------------------------------- #
    # Generate the payload for the challenge response
    # ------------------------------------------------------------------------------- #

    def generate_challenge_payload(self, challenge_data, resp):
        try:
            # Extract required tokens from the page
            r_token = re.search(r'name="r" value="([^"]+)"', resp.text)
            if not r_token:
                raise CloudflareChallengeError("Could not find 'r' token")
                
            # Generate a random payload
            payload = {
                'r': r_token.group(1),
                'cf_ch_verify': 'plat',
                'vc': '',
                'captcha_vc': '',
                'cf_captcha_kind': 'h',
                'h-captcha-response': ''
            }
            
            # Add challenge-specific data
            if 'cvId' in challenge_data:
                payload['cv_chal_id'] = challenge_data['cvId']
                
            if 'chlPageData' in challenge_data:
                payload['cf_chl_page_data'] = challenge_data['chlPageData']
                
            return payload
            
        except Exception as e:
            logging.error(f"Error generating Cloudflare challenge payload: {str(e)}")
            raise CloudflareChallengeError(f"Error generating Cloudflare challenge payload: {str(e)}")

    # ------------------------------------------------------------------------------- #
    # Handle the Cloudflare v2 challenge
    # ------------------------------------------------------------------------------- #

    def handle_V2_Challenge(self, resp, **kwargs):
        try:
            # Extract challenge data
            challenge_info = self.extract_challenge_data(resp)
            
            # Wait for the specified delay
            time.sleep(self.delay)
            
            # Generate the challenge payload
            payload = self.generate_challenge_payload(challenge_info['challenge_data'], resp)
            
            # Prepare the request
            url_parsed = urlparse(resp.url)
            challenge_url = f"{url_parsed.scheme}://{url_parsed.netloc}{challenge_info['form_action']}"
            
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
                raise CloudflareSolveError("Failed to solve Cloudflare v2 challenge")
                
            return challenge_response
            
        except Exception as e:
            logging.error(f"Error handling Cloudflare v2 challenge: {str(e)}")
            raise CloudflareChallengeError(f"Error handling Cloudflare v2 challenge: {str(e)}")

    # ------------------------------------------------------------------------------- #
    # Handle the Cloudflare v2 captcha challenge
    # ------------------------------------------------------------------------------- #

    def handle_V2_Captcha_Challenge(self, resp, **kwargs):
        try:
            # Check if captcha provider is configured
            if (
                not self.cloudscraper.captcha
                or not isinstance(self.cloudscraper.captcha, dict)
                or not self.cloudscraper.captcha.get('provider')
            ):
                self.cloudscraper.simpleException(
                    CloudflareCaptchaProvider,
                    "Cloudflare Captcha detected, but no captcha provider configured"
                )
                
            # Extract challenge data
            challenge_info = self.extract_challenge_data(resp)
            
            # Extract the site key
            site_key = re.search(
                r'data-sitekey="([^"]+)"',
                resp.text
            )
            
            if not site_key:
                raise CloudflareCaptchaError("Could not find hCaptcha site key")
                
            # Generate the challenge payload
            payload = self.generate_challenge_payload(challenge_info['challenge_data'], resp)
            
            # Solve the captcha
            captcha_response = Captcha.dynamicImport(
                self.cloudscraper.captcha.get('provider').lower()
            ).solveCaptcha(
                'hCaptcha',
                resp.url,
                site_key.group(1),
                self.cloudscraper.captcha
            )
            
            # Add the captcha response to the payload
            payload['h-captcha-response'] = captcha_response
            
            # Prepare the request
            url_parsed = urlparse(resp.url)
            challenge_url = f"{url_parsed.scheme}://{url_parsed.netloc}{challenge_info['form_action']}"
            
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
                raise CloudflareSolveError("Failed to solve Cloudflare v2 captcha challenge")
                
            return challenge_response
            
        except Exception as e:
            logging.error(f"Error handling Cloudflare v2 captcha challenge: {str(e)}")
            raise CloudflareCaptchaError(f"Error handling Cloudflare v2 captcha challenge: {str(e)}")
