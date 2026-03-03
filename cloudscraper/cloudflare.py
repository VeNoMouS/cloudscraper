# -*- coding: utf-8 -*-
"""
cloudscraper.cloudflare
=======================

This module contains the CloudflareV1 challenge handler for legacy v1 challenges.

Classes:
    - CloudflareV1: Handler for Cloudflare v1 (IUAM) challenges
"""

from __future__ import annotations

import html
import logging
import re
import time
from collections import OrderedDict
from typing import TYPE_CHECKING, Any, Dict, Optional

from urllib.parse import urlparse, urljoin

from .base import ChallengeHandler
from .constants import (
    CHALLENGE_FORM_PATTERN,
    CAPTCHA_TRACE_PATTERN,
    JSCH_TRACE_PATTERN,
    CF_ERROR_1020_PATTERN,
    CLOUDFLARE_CHALLENGE_STATUS_CODES,
    DEFAULT_REQUEST_DELAY
)
from .exceptions import (
    CloudflareCode1020,
    CloudflareIUAMError,
    CloudflareSolveError,
    CloudflareChallengeError,
    CloudflareCaptchaError,
    CloudflareCaptchaProvider
)
from .captcha import Captcha
from .interpreters import JavaScriptInterpreter

if TYPE_CHECKING:
    from requests import Response


logger = logging.getLogger(__name__)


# Pre-compiled regex patterns for better performance
_RE_CHALLENGE_FORM = re.compile(CHALLENGE_FORM_PATTERN, re.M | re.S)
_RE_CAPTCHA_TRACE = re.compile(CAPTCHA_TRACE_PATTERN, re.M | re.S)
_RE_J_SCH_TRACE = re.compile(JSCH_TRACE_PATTERN, re.M | re.S)
_RE_ERROR_1020 = re.compile(CF_ERROR_1020_PATTERN, re.M | re.DOTALL)
_RE_NEW_CHALLENGE = re.compile(r'cpo.src\s*=\s*[\'"]/cdn-cgi/challenge-platform/\S+orchestrate/jsch/v1', re.M | re.S)
_RE_NEW_CAPTCHA = re.compile(r'cpo.src\s*=\s*[\'"]/cdn-cgi/challenge-platform/\S+orchestrate/(captcha|managed)/v1', re.M | re.S)
_RE_DELAY = re.compile(r'submit\(\);\r?\n\s*\},\s*([0-9]+)', re.M | re.S)
_RE_INPUT_FIELD = re.compile(r'^\s*<input\s(.*?)/>', re.M | re.S)
_RE_FORM_PAYLOAD = re.compile(
    r'<form (?P<form>.*?="challenge-form" '
    r'action="(?P<challengeUUID>.*?'
    r'__cf_chl_f_tk=\S+)"(.*?)</form>)',
    re.M | re.DOTALL
)
_RE_CAPTCHA_FORM = re.compile(
    r'<form (?P<form>.*?="challenge-form" '
    r'action="(?P<challengeUUID>.*?__cf_chl_captcha_tk__=\S+)"(.*?)</form>)',
    re.M | re.DOTALL
)


class CloudflareV1(ChallengeHandler):
    """
    Handler for Cloudflare v1 (IUAM - I'm Under Attack Mode) challenges.
    
    This handler manages:
    - JavaScript challenge solving
    - CAPTCHA challenge solving (via external providers)
    - Challenge response submission
    
    Attributes:
        cloudscraper: Reference to the parent CloudScraper instance
        delay: Delay in seconds before solving the challenge
    """
    
    def __init__(self, cloudscraper: Any, delay: Optional[float] = None) -> None:
        """
        Initialize the CloudflareV1 handler.
        
        Args:
            cloudscraper: Reference to the parent CloudScraper instance
            delay: Optional delay override in seconds
        """
        super().__init__(cloudscraper, delay)
    
    def is_challenge(self, resp: Response) -> bool:
        """
        Check if the response contains a Cloudflare v1 challenge.
        
        Args:
            resp: The HTTP response to check
            
        Returns:
            True if the response contains a v1 challenge, False otherwise
        """
        return (
            self._is_iuam_challenge(resp) or 
            self._is_captcha_challenge(resp)
        )
    
    @staticmethod
    def _is_iuam_challenge(resp: Response) -> bool:
        """Check for IUAM challenge pattern."""
        try:
            return (
                resp.headers.get('Server', '').startswith('cloudflare')
                and resp.status_code in CLOUDFLARE_CHALLENGE_STATUS_CODES
                and _RE_J_SCH_TRACE.search(resp.text)
                and _RE_CHALLENGE_FORM.search(resp.text)
            )
        except AttributeError:
            logger.debug("Error checking IUAM challenge: %s", getattr(resp, 'status_code', 'unknown'))
        return False
    
    @staticmethod
    def _is_captcha_challenge(resp: Response) -> bool:
        """Check for CAPTCHA challenge pattern."""
        try:
            return (
                resp.headers.get('Server', '').startswith('cloudflare')
                and resp.status_code == 403
                and _RE_CAPTCHA_TRACE.search(resp.text)
                and _RE_CHALLENGE_FORM.search(resp.text)
            )
        except AttributeError:
            logger.debug("Error checking CAPTCHA challenge: %s", getattr(resp, 'status_code', 'unknown'))
        return False
    
    @staticmethod
    def _is_firewall_blocked(resp: Response) -> bool:
        """Check for Firewall 1020 error."""
        try:
            return (
                resp.headers.get('Server', '').startswith('cloudflare')
                and resp.status_code == 403
                and _RE_ERROR_1020.search(resp.text)
            )
        except AttributeError:
            logger.debug("Error checking firewall block: %s", getattr(resp, 'status_code', 'unknown'))
        return False
    
    def _check_challenge_type(self, resp: Response) -> None:
        """
        Check and raise exceptions for specific challenge types.
        
        Args:
            resp: The HTTP response to check
            
        Raises:
            CloudflareCode1020: If firewall blocked (code 1020)
            CloudflareChallengeError: If new v2 challenge detected (not supported in open source)
        """
        if self._is_firewall_blocked(resp):
            self.cloudscraper.simpleException(
                CloudflareCode1020,
                'Cloudflare has blocked this request (Code 1020 Detected).'
            )
        
        # Check for new v2 challenges (not supported in open source)
        try:
            if _RE_NEW_CAPTCHA.search(resp.text):
                self.cloudscraper.simpleException(
                    CloudflareChallengeError,
                    'Detected a Cloudflare version 2 Captcha challenge, This feature is not available in the opensource (free) version.'
                )
            
            if _RE_NEW_CHALLENGE.search(resp.text):
                self.cloudscraper.simpleException(
                    CloudflareChallengeError,
                    'Detected a Cloudflare version 2 challenge, This feature is not available in the opensource (free) version.'
                )
        except AttributeError:
            pass
    
    def handle_challenge(self, resp: Response, **kwargs: Any) -> Response:
        """
        Handle and solve the Cloudflare v1 challenge.
        
        Args:
            resp: The HTTP response containing the challenge
            **kwargs: Additional arguments for the challenge solver
            
        Returns:
            The response after successfully solving the challenge
        """
        # First check for specific challenge types
        self._check_challenge_type(resp)
        
        if self._is_captcha_challenge(resp):
            return self._handle_captcha_challenge(resp, **kwargs)
        else:
            return self._handle_iuam_challenge(resp, **kwargs)
    
    def _handle_iuam_challenge(self, resp: Response, **kwargs: Any) -> Response:
        """Handle IUAM (JavaScript) challenge."""
        # Double down on the request as some websites check cfuid before issuing challenge
        if getattr(self.cloudscraper, 'doubleDown', True):
            resp = self.cloudscraper.decodeBrotli(
                self.cloudscraper.perform_request(resp.request.method, resp.url, **kwargs)
            )
        
        # Re-check if challenge still exists
        if not self._is_iuam_challenge(resp):
            return resp
        
        # Get challenge delay
        delay = self._extract_delay(resp.text)
        if delay:
            time.sleep(delay)
        
        # Solve the challenge
        submit_url = self._solve_iuam_challenge(resp.text, resp.url)
        
        # Submit challenge response
        return self._submit_challenge_response(resp, submit_url, **kwargs)
    
    def _handle_captcha_challenge(self, resp: Response, **kwargs: Any) -> Response:
        """Handle CAPTCHA challenge."""
        # Double down on the request
        if getattr(self.cloudscraper, 'doubleDown', True):
            resp = self.cloudscraper.decodeBrotli(
                self.cloudscraper.perform_request(resp.request.method, resp.url, **kwargs)
            )
        
        # Re-check if challenge still exists
        if not self._is_captcha_challenge(resp):
            return resp
        
        # Check for captcha provider
        captcha_config = getattr(self.cloudscraper, 'captcha', {})
        if not captcha_config or not isinstance(captcha_config, dict) or not captcha_config.get('provider'):
            self.cloudscraper.simpleException(
                CloudflareCaptchaProvider,
                "Cloudflare Captcha detected, unfortunately you haven't loaded an anti Captcha provider "
                "correctly via the 'captcha' parameter."
            )
        
        # Return response without solving if provider is 'return_response'
        if captcha_config.get('provider') == 'return_response':
            return resp
        
        # Solve CAPTCHA
        submit_url = self._solve_captcha_challenge(resp.text, resp.url)
        
        # Submit challenge response
        return self._submit_challenge_response(resp, submit_url, **kwargs)
    
    def _extract_delay(self, body: str) -> Optional[float]:
        """
        Extract the challenge delay from the page.
        
        Args:
            body: HTML body of the challenge page
            
        Returns:
            Delay in seconds, or None if not found
        """
        try:
            match = _RE_DELAY.search(body)
            if match:
                return float(match.group(1)) / float(1000)
        except (AttributeError, ValueError) as e:
            logger.warning("Error extracting delay: %s", e)
        return None
    
    def _solve_iuam_challenge(self, body: str, url: str) -> Dict[str, Any]:
        """
        Solve the IUAM JavaScript challenge.
        
        Args:
            body: HTML body of the challenge page
            url: Original request URL
            
        Returns:
            Dictionary with 'url' and 'data' keys for the challenge submission
            
        Raises:
            CloudflareIUAMError: If challenge parameters cannot be extracted
        """
        try:
            form_match = _RE_FORM_PAYLOAD.search(body)
            if not form_match:
                raise CloudflareIUAMError("Cloudflare IUAM detected, unfortunately we can't extract the parameters correctly.")
            
            form_payload = form_match.groupdict()
            
            if not all(key in form_payload for key in ['form', 'challengeUUID']):
                raise CloudflareIUAMError("Cloudflare IUAM detected, unfortunately we can't extract the parameters correctly.")
            
            # Extract payload fields
            payload = OrderedDict()
            for challenge_param in _RE_INPUT_FIELD.findall(form_payload['form']):
                input_payload = dict(re.findall(r'(\S+)="(\S+)"', challenge_param))
                if input_payload.get('name') in ['r', 'jschl_vc', 'pass']:
                    payload[input_payload['name']] = input_payload['value']
            
            # Solve JavaScript challenge
            host_parsed = urlparse(url)
            interpreter = getattr(self.cloudscraper, 'interpreter', 'js2py')
            
            payload['jschl_answer'] = JavaScriptInterpreter.dynamicImport(
                interpreter
            ).solveChallenge(body, host_parsed.netloc)
            
            return {
                'url': f"{host_parsed.scheme}://{host_parsed.netloc}{html.unescape(form_payload['challengeUUID'])}",
                'data': payload
            }
            
        except AttributeError as e:
            raise CloudflareIUAMError(f"Cloudflare IUAM detected, unfortunately we can't extract the parameters correctly: {e}")
    
    def _solve_captcha_challenge(self, body: str, url: str) -> Dict[str, Any]:
        """
        Solve the CAPTCHA challenge using external provider.
        
        Args:
            body: HTML body of the challenge page
            url: Original request URL
            
        Returns:
            Dictionary with 'url' and 'data' keys for the challenge submission
            
        Raises:
            CloudflareCaptchaError: If challenge parameters cannot be extracted
        """
        try:
            form_match = _RE_CAPTCHA_FORM.search(body)
            if not form_match:
                raise CloudflareCaptchaError("Cloudflare Captcha detected, unfortunately we can't extract the parameters correctly.")
            
            form_payload = form_match.groupdict()
            
            if not all(key in form_payload for key in ['form', 'challengeUUID']):
                raise CloudflareCaptchaError("Cloudflare Captcha detected, unfortunately we can't extract the parameters correctly.")
            
            # Extract payload fields
            payload = OrderedDict(
                re.findall(
                    r'(name="r"\svalue|data-ray|data-sitekey|name="cf_captcha_kind"\svalue)="(.*?)"',
                    form_payload['form']
                )
            )
            
            captcha_type = 'reCaptcha' if payload.get('name="cf_captcha_kind" value') == 're' else 'hCaptcha'
            
        except (AttributeError, KeyError) as e:
            raise CloudflareCaptchaError(f"Cloudflare Captcha detected, unfortunately we can't extract the parameters correctly: {e}")
        
        # Get captcha config
        captcha_config = self.cloudscraper.captcha
        
        # Pass proxy parameter if available
        proxies = getattr(self.cloudscraper, 'proxies', None)
        if proxies and proxies != captcha_config.get('proxy'):
            captcha_config['proxy'] = proxies
        
        # Pass User-Agent
        captcha_config['User-Agent'] = self.cloudscraper.headers.get('User-Agent', '')
        
        # Solve captcha
        provider = captcha_config.get('provider', '').lower()
        captcha_response = Captcha.dynamicImport(provider).solveCaptcha(
            captcha_type,
            url,
            payload.get('data-sitekey'),
            captcha_config
        )
        
        # Build final payload
        data_payload = OrderedDict([
            ('r', payload.get('name="r" value', '')),
            ('cf_captcha_kind', payload.get('name="cf_captcha_kind" value', '')),
            ('id', payload.get('data-ray', '')),
            ('g-recaptcha-response', captcha_response)
        ])
        
        if captcha_type == 'hCaptcha':
            data_payload['h-captcha-response'] = captcha_response
        
        host_parsed = urlparse(url)
        
        return {
            'url': f"{host_parsed.scheme}://{host_parsed.netloc}{html.unescape(form_payload['challengeUUID'])}",
            'data': data_payload
        }
    
    def _submit_challenge_response(
        self, 
        resp: Response, 
        submit_url: Dict[str, Any],
        **kwargs: Any
    ) -> Response:
        """
        Submit the challenge response to Cloudflare.
        
        Args:
            resp: Original challenge response
            submit_url: Dictionary with 'url' and 'data' keys
            **kwargs: Additional request arguments
            
        Returns:
            Final response after challenge submission
        """
        from copy import deepcopy
        
        def update_attr(obj: Dict, name: str, new_value: Any) -> Dict:
            """Helper to update nested dictionary attributes."""
            try:
                obj[name].update(new_value)
                return obj[name]
            except (AttributeError, KeyError):
                obj[name] = {}
                obj[name].update(new_value)
                return obj[name]
        
        cloudflare_kwargs = deepcopy(kwargs)
        cloudflare_kwargs['allow_redirects'] = False
        cloudflare_kwargs['data'] = update_attr(cloudflare_kwargs, 'data', submit_url['data'])
        
        url_parsed = urlparse(resp.url)
        cloudflare_kwargs['headers'] = update_attr(
            cloudflare_kwargs,
            'headers',
            {
                'Origin': f'{url_parsed.scheme}://{url_parsed.netloc}',
                'Referer': resp.url
            }
        )
        
        # Submit challenge
        challenge_submit_response = self.cloudscraper.request(
            'POST',
            submit_url['url'],
            **cloudflare_kwargs
        )
        
        if challenge_submit_response.status_code == 400:
            self.cloudscraper.simpleException(
                CloudflareSolveError,
                'Invalid challenge answer detected, Cloudflare broken?'
            )
        
        # Handle response
        if not challenge_submit_response.is_redirect:
            return challenge_submit_response
        
        # Follow redirect
        cloudflare_kwargs = deepcopy(kwargs)
        redirect_location = challenge_submit_response.headers.get('Location', '')
        
        if not urlparse(redirect_location).netloc:
            redirect_location = urljoin(challenge_submit_response.url, redirect_location)
        
        cloudflare_kwargs['headers'] = update_attr(
            cloudflare_kwargs,
            'headers',
            {'Referer': challenge_submit_response.url}
        )
        
        return self.cloudscraper.request(
            resp.request.method,
            redirect_location,
            **cloudflare_kwargs
        )
