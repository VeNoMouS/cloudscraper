# -*- coding: utf-8 -*-
"""
cloudscraper.turnstile
=====================

This module contains the CloudflareTurnstile challenge handler.

Classes:
    - CloudflareTurnstile: Handler for Cloudflare Turnstile challenges
"""

from __future__ import annotations

import logging
import random
import re
import time
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Dict, Optional

from urllib.parse import urlparse

from .base import ChallengeHandler
from .constants import (
    CLOUDFLARE_CHALLENGE_STATUS_CODES,
    DEFAULT_REQUEST_DELAY
)
from .exceptions import (
    CloudflareSolveError,
    CloudflareCaptchaProvider,
    CloudflareTurnstileError
)
from .captcha import Captcha

if TYPE_CHECKING:
    from requests import Response


logger = logging.getLogger(__name__)


# Pre-compiled regex patterns
_RE_TURNSTILE_CLASS = re.compile(r'class="cf-turnstile"', re.M | re.S)
_RE_TURNSTILE_API = re.compile(r'src="https://challenges.cloudflare.com/turnstile/v0/api.js', re.M | re.S)
_RE_TURNSTILE_SITEKEY = re.compile(r'data-sitekey="([0-9A-Za-z]{40})"', re.M | re.S)
_RE_FORM_ACTION = re.compile(r'<form .*?action="([^"]+)"', re.DOTALL)
_RE_INPUT_FIELDS = re.compile(r'<input[^>]*name="([^"]+)"[^>]*value="([^"]*)"')


class CloudflareTurnstile(ChallengeHandler):
    """
    Handler for Cloudflare Turnstile challenges.
    
    Turnstile is Cloudflare's CAPTCHA alternative that provides
    invisible challenge verification.
    
    Attributes:
        cloudscraper: Reference to the parent CloudScraper instance
        delay: Delay in seconds before solving the challenge
    """
    
    def __init__(self, cloudscraper: Any, delay: Optional[float] = None) -> None:
        """
        Initialize the CloudflareTurnstile handler.
        
        Args:
            cloudscraper: Reference to the parent CloudScraper instance
            delay: Optional delay override in seconds
        """
        super().__init__(cloudscraper, delay)
        self.delay = delay or getattr(cloudscraper, 'delay', None) or random.uniform(1.0, 5.0)
    
    def is_challenge(self, resp: Response) -> bool:
        """
        Check if the response contains a Cloudflare Turnstile challenge.
        
        Args:
            resp: The HTTP response to check
            
        Returns:
            True if the response contains a Turnstile challenge, False otherwise
        """
        try:
            return (
                resp.headers.get('Server', '').startswith('cloudflare')
                and resp.status_code in CLOUDFLARE_CHALLENGE_STATUS_CODES
                and (
                    _RE_TURNSTILE_CLASS.search(resp.text)
                    or _RE_TURNSTILE_API.search(resp.text)
                    or _RE_TURNSTILE_SITEKEY.search(resp.text)
                )
            )
        except AttributeError:
            logger.debug("Error checking Turnstile challenge: %s", getattr(resp, 'status_code', 'unknown'))
        return False
    
    def handle_challenge(self, resp: Response, **kwargs: Any) -> Response:
        """
        Handle and solve the Cloudflare Turnstile challenge.
        
        Args:
            resp: The HTTP response containing the challenge
            **kwargs: Additional arguments for the challenge solver
            
        Returns:
            The response after successfully solving the challenge
            
        Raises:
            CloudflareCaptchaProvider: If no captcha provider is configured
            CloudflareTurnstileError: If Turnstile cannot be solved
        """
        try:
            # Check for captcha provider
            captcha_config = getattr(self.cloudscraper, 'captcha', {})
            if not captcha_config or not isinstance(captcha_config, dict) or not captcha_config.get('provider'):
                self.cloudscraper.simpleException(
                    CloudflareCaptchaProvider,
                    "Cloudflare Turnstile detected, but no captcha provider configured"
                )
            
            # Extract Turnstile data
            turnstile_info = self._extract_turnstile_data(resp)
            
            # Wait for delay
            time.sleep(self.delay)
            
            # Solve Turnstile
            provider = captcha_config.get('provider', '').lower()
            turnstile_response = Captcha.dynamicImport(provider).solveCaptcha(
                'turnstile',
                resp.url,
                turnstile_info['site_key'],
                captcha_config
            )
            
            # Prepare payload
            payload = {
                'cf-turnstile-response': turnstile_response
            }
            
            # Add additional form fields
            for field_match in _RE_INPUT_FIELDS.finditer(resp.text):
                field_name, field_value = field_match.groups()
                if field_name != 'cf-turnstile-response':
                    payload[field_name] = field_value
            
            # Prepare request
            url_parsed = urlparse(resp.url)
            challenge_url = turnstile_info['form_action']
            if not challenge_url.startswith('http'):
                challenge_url = f"{url_parsed.scheme}://{url_parsed.netloc}{challenge_url}"
            
            cloudflare_kwargs = deepcopy(kwargs)
            cloudflare_kwargs['allow_redirects'] = False
            
            # Update headers
            cloudflare_kwargs['headers'] = cloudflare_kwargs.get('headers', {})
            cloudflare_kwargs['headers'].update({
                'Origin': f'{url_parsed.scheme}://{url_parsed.netloc}',
                'Referer': resp.url,
                'Content-Type': 'application/x-www-form-urlencoded'
            })
            
            # Submit challenge
            challenge_response = self.cloudscraper.request(
                'POST',
                challenge_url,
                data=payload,
                **cloudflare_kwargs
            )
            
            if challenge_response.status_code == 403:
                raise CloudflareSolveError("Failed to solve Cloudflare Turnstile challenge")
            
            return challenge_response
            
        except (CloudflareCaptchaProvider, CloudflareTurnstileError):
            raise
        except Exception as e:
            logger.error("Error handling Cloudflare Turnstile challenge: %s", str(e))
            raise CloudflareTurnstileError(f"Error handling Cloudflare Turnstile challenge: {e}")
    
    def _extract_turnstile_data(self, resp: Response) -> Dict[str, str]:
        """
        Extract Turnstile challenge data from the response.
        
        Args:
            resp: HTTP response containing the challenge
            
        Returns:
            Dictionary with site_key and form_action
            
        Raises:
            CloudflareTurnstileError: If Turnstile data cannot be extracted
        """
        try:
            # Extract site key
            site_key_match = _RE_TURNSTILE_SITEKEY.search(resp.text)
            if not site_key_match:
                raise CloudflareTurnstileError("Could not find Turnstile site key")
            
            # Extract form action
            form_match = _RE_FORM_ACTION.search(resp.text)
            
            if form_match:
                form_action_url = form_match.group(1)
            else:
                # Use current URL if no form action found
                url_parsed = urlparse(resp.url)
                form_action_url = f"{url_parsed.scheme}://{url_parsed.netloc}{url_parsed.path}"
            
            return {
                'site_key': site_key_match.group(1),
                'form_action': form_action_url
            }
            
        except CloudflareTurnstileError:
            raise
        except Exception as e:
            logger.error("Error extracting Cloudflare Turnstile data: %s", str(e))
            raise CloudflareTurnstileError(f"Error extracting Cloudflare Turnstile data: {e}")
