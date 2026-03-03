# -*- coding: utf-8 -*-
"""
cloudscraper.cloudflare_v2
==========================

This module contains the CloudflareV2 challenge handler.

Classes:
    - CloudflareV2: Handler for Cloudflare v2 challenges

Note:
    Some v2 challenges are not available in the open source version.
"""

from __future__ import annotations

import json
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
    CloudflareChallengeError,
    CloudflareSolveError,
    CloudflareCaptchaError,
    CloudflareCaptchaProvider
)
from .captcha import Captcha

if TYPE_CHECKING:
    from requests import Response


logger = logging.getLogger(__name__)


# Pre-compiled regex patterns
_RE_V2_CHALLENGE = re.compile(
    r'cpo\.src\s*=\s*[\'"]/cdn-cgi/challenge-platform/\S+orchestrate/jsch/v1',
    re.M | re.S
)
_RE_V2_CAPTCHA = re.compile(
    r'cpo\.src\s*=\s*[\'"]/cdn-cgi/challenge-platform/\S+orchestrate/(captcha|managed)/v1',
    re.M | re.S
)
_RE_CHALLENGE_DATA = re.compile(r'window\._cf_chl_opt=({.*?});', re.DOTALL)
_RE_FORM_ACTION = re.compile(r'<form .*?id="challenge-form" action="([^"]+)"', re.DOTALL)
_RE_R_TOKEN = re.compile(r'name="r" value="([^"]+)"')


class CloudflareV2(ChallengeHandler):
    """
    Handler for Cloudflare v2 challenges.
    
    Note:
        Some v2 challenges require the commercial version.
        This handler supports basic v2 JavaScript and CAPTCHA challenges.
    
    Attributes:
        cloudscraper: Reference to the parent CloudScraper instance
        delay: Delay in seconds before solving the challenge
    """
    
    def __init__(self, cloudscraper: Any, delay: Optional[float] = None) -> None:
        """
        Initialize the CloudflareV2 handler.
        
        Args:
            cloudscraper: Reference to the parent CloudScraper instance
            delay: Optional delay override in seconds
        """
        super().__init__(cloudscraper, delay)
        self.delay = delay or getattr(cloudscraper, 'delay', None) or random.uniform(1.0, 5.0)
    
    def is_challenge(self, resp: Response) -> bool:
        """
        Check if the response contains a Cloudflare v2 challenge.
        
        Args:
            resp: The HTTP response to check
            
        Returns:
            True if the response contains a v2 challenge, False otherwise
        """
        return self._is_v2_challenge(resp) or self._is_v2_captcha_challenge(resp)
    
    @staticmethod
    def _is_v2_challenge(resp: Response) -> bool:
        """Check for v2 JavaScript challenge pattern."""
        try:
            return (
                resp.headers.get('Server', '').startswith('cloudflare')
                and resp.status_code in CLOUDFLARE_CHALLENGE_STATUS_CODES
                and _RE_V2_CHALLENGE.search(resp.text)
            )
        except AttributeError:
            logger.debug("Error checking v2 challenge: %s", getattr(resp, 'status_code', 'unknown'))
        return False
    
    @staticmethod
    def _is_v2_captcha_challenge(resp: Response) -> bool:
        """Check for v2 CAPTCHA challenge pattern."""
        try:
            return (
                resp.headers.get('Server', '').startswith('cloudflare')
                and resp.status_code == 403
                and _RE_V2_CAPTCHA.search(resp.text)
            )
        except AttributeError:
            logger.debug("Error checking v2 captcha: %s", getattr(resp, 'status_code', 'unknown'))
        return False
    
    def handle_challenge(self, resp: Response, **kwargs: Any) -> Response:
        """
        Handle and solve the Cloudflare v2 challenge.
        
        Args:
            resp: The HTTP response containing the challenge
            **kwargs: Additional arguments for the challenge solver
            
        Returns:
            The response after successfully solving the challenge
            
        Raises:
            CloudflareChallengeError: If challenge cannot be solved
        """
        if self._is_v2_captcha_challenge(resp):
            return self._handle_v2_captcha(resp, **kwargs)
        else:
            return self._handle_v2_challenge(resp, **kwargs)
    
    def _extract_challenge_data(self, resp: Response) -> Dict[str, Any]:
        """
        Extract challenge data from the response.
        
        Args:
            resp: HTTP response containing the challenge
            
        Returns:
            Dictionary with challenge_data and form_action
            
        Raises:
            CloudflareChallengeError: If challenge data cannot be extracted
        """
        try:
            # Extract challenge data
            challenge_match = _RE_CHALLENGE_DATA.search(resp.text)
            if not challenge_match:
                raise CloudflareChallengeError("Could not find Cloudflare challenge data")
            
            challenge_data = json.loads(challenge_match.group(1))
            
            # Extract form action
            form_match = _RE_FORM_ACTION.search(resp.text)
            if not form_match:
                raise CloudflareChallengeError("Could not find Cloudflare challenge form")
            
            return {
                'challenge_data': challenge_data,
                'form_action': form_match.group(1)
            }
            
        except json.JSONDecodeError as e:
            raise CloudflareChallengeError(f"Error parsing challenge data: {e}")
        except Exception as e:
            logger.error("Error extracting Cloudflare challenge data: %s", str(e))
            raise CloudflareChallengeError(f"Error extracting Cloudflare challenge data: {e}")
    
    def _generate_payload(self, challenge_data: Dict[str, Any], resp: Response) -> Dict[str, str]:
        """
        Generate the payload for challenge submission.
        
        Args:
            challenge_data: Extracted challenge data
            resp: HTTP response
            
        Returns:
            Payload dictionary
            
        Raises:
            CloudflareChallengeError: If required tokens cannot be found
        """
        try:
            r_match = _RE_R_TOKEN.search(resp.text)
            if not r_match:
                raise CloudflareChallengeError("Could not find 'r' token")
            
            payload = {
                'r': r_match.group(1),
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
            logger.error("Error generating Cloudflare challenge payload: %s", str(e))
            raise CloudflareChallengeError(f"Error generating Cloudflare challenge payload: {e}")
    
    def _handle_v2_challenge(self, resp: Response, **kwargs: Any) -> Response:
        """
        Handle Cloudflare v2 JavaScript challenge.
        
        Args:
            resp: HTTP response containing the challenge
            **kwargs: Additional request arguments
            
        Returns:
            Response after solving the challenge
        """
        try:
            # Extract challenge data
            challenge_info = self._extract_challenge_data(resp)
            
            # Wait for delay
            time.sleep(self.delay)
            
            # Generate payload
            payload = self._generate_payload(challenge_info['challenge_data'], resp)
            
            # Prepare request
            url_parsed = urlparse(resp.url)
            challenge_url = f"{url_parsed.scheme}://{url_parsed.netloc}{challenge_info['form_action']}"
            
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
                raise CloudflareSolveError("Failed to solve Cloudflare v2 challenge")
            
            return challenge_response
            
        except CloudflareChallengeError:
            raise
        except Exception as e:
            logger.error("Error handling Cloudflare v2 challenge: %s", str(e))
            raise CloudflareChallengeError(f"Error handling Cloudflare v2 challenge: {e}")
    
    def _handle_v2_captcha(self, resp: Response, **kwargs: Any) -> Response:
        """
        Handle Cloudflare v2 CAPTCHA challenge.
        
        Args:
            resp: HTTP response containing the challenge
            **kwargs: Additional request arguments
            
        Returns:
            Response after solving the challenge
            
        Raises:
            CloudflareCaptchaProvider: If no captcha provider is configured
            CloudflareCaptchaError: If captcha solving fails
        """
        try:
            # Check for captcha provider
            captcha_config = getattr(self.cloudscraper, 'captcha', {})
            if not captcha_config or not isinstance(captcha_config, dict) or not captcha_config.get('provider'):
                self.cloudscraper.simpleException(
                    CloudflareCaptchaProvider,
                    "Cloudflare Captcha detected, but no captcha provider configured"
                )
            
            # Extract challenge data
            challenge_info = self._extract_challenge_data(resp)
            
            # Extract site key
            site_key_match = re.search(r'data-sitekey="([^"]+)"', resp.text)
            if not site_key_match:
                raise CloudflareCaptchaError("Could not find hCaptcha site key")
            
            # Generate payload
            payload = self._generate_payload(challenge_info['challenge_data'], resp)
            
            # Solve captcha
            provider = captcha_config.get('provider', '').lower()
            captcha_response = Captcha.dynamicImport(provider).solveCaptcha(
                'hCaptcha',
                resp.url,
                site_key_match.group(1),
                captcha_config
            )
            
            # Add captcha response to payload
            payload['h-captcha-response'] = captcha_response
            
            # Prepare request
            url_parsed = urlparse(resp.url)
            challenge_url = f"{url_parsed.scheme}://{url_parsed.netloc}{challenge_info['form_action']}"
            
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
                raise CloudflareSolveError("Failed to solve Cloudflare v2 captcha challenge")
            
            return challenge_response
            
        except (CloudflareCaptchaProvider, CloudflareCaptchaError):
            raise
        except Exception as e:
            logger.error("Error handling Cloudflare v2 captcha challenge: %s", str(e))
            raise CloudflareCaptchaError(f"Error handling Cloudflare v2 captcha challenge: {e}")
