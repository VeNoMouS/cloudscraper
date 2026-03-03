# -*- coding: utf-8 -*-
"""
cloudscraper.request_throttler
==============================

This module contains the RequestThrottler class for managing request rate limiting
and concurrent request handling.

Classes:
    - RequestThrottler: Manages request throttling and concurrency control
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any, Optional

from .constants import (
    DEFAULT_MIN_REQUEST_INTERVAL,
    DEFAULT_MAX_CONCURRENT_REQUESTS
)

if TYPE_CHECKING:
    from requests import Response


logger = logging.getLogger(__name__)


class RequestThrottler:
    """
    Manages request throttling and concurrent request handling.
    
    This class is responsible for:
    - Enforcing minimum interval between requests
    - Limiting concurrent requests
    - TLS cipher suite rotation for anti-detection
    
    Attributes:
        min_request_interval: Minimum seconds between requests
        max_concurrent_requests: Maximum concurrent requests allowed
        current_concurrent_requests: Current number of concurrent requests
        last_request_time: Timestamp of the last request
    """
    
    def __init__(
        self,
        cloudscraper: Any,
        min_request_interval: float = DEFAULT_MIN_REQUEST_INTERVAL,
        max_concurrent_requests: int = DEFAULT_MAX_CONCURRENT_REQUESTS,
        rotate_tls_ciphers: bool = True
    ) -> None:
        """
        Initialize the RequestThrottler.
        
        Args:
            cloudscraper: Reference to the parent CloudScraper instance
            min_request_interval: Minimum seconds between requests
            max_concurrent_requests: Maximum concurrent requests allowed
            rotate_tls_ciphers: Whether to rotate TLS cipher suites
        """
        self.cloudscraper = cloudscraper
        self.min_request_interval = min_request_interval
        self.max_concurrent_requests = max_concurrent_requests
        self.rotate_tls_ciphers = rotate_tls_ciphers
        
        # Initialize tracking
        self.last_request_time = 0
        self.current_concurrent_requests = 0
        self._cipher_rotation_count = 0
    
    def acquire(self) -> None:
        """
        Acquire permission to make a request, applying throttling if needed.
        
        This method will block until:
        - The minimum interval since the last request has passed
        - The number of concurrent requests is below the limit
        """
        self._apply_interval_throttling()
        self._apply_concurrency_limit()
        
        # Update last request time
        self.last_request_time = time.time()
        
        # Increment concurrent request counter
        self.current_concurrent_requests += 1
        
        # Rotate TLS ciphers if enabled
        if self.rotate_tls_ciphers:
            self._rotate_tls_cipher_suite()
    
    def release(self) -> None:
        """
        Release a request slot after the request is complete.
        """
        if self.current_concurrent_requests > 0:
            self.current_concurrent_requests -= 1
    
    def _apply_interval_throttling(self) -> None:
        """
        Apply throttling based on minimum interval between requests.
        """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            if self.cloudscraper.debug:
                logger.debug(f'Request throttling: sleeping {sleep_time:.2f}s')
            time.sleep(sleep_time)
    
    def _apply_concurrency_limit(self) -> None:
        """
        Wait if too many concurrent requests are in progress.
        """
        while self.current_concurrent_requests >= self.max_concurrent_requests:
            if self.cloudscraper.debug:
                logger.debug(
                    f'Concurrent request limit reached '
                    f'({self.current_concurrent_requests}/{self.max_concurrent_requests}), waiting...'
                )
            time.sleep(0.1)
    
    def _rotate_tls_cipher_suite(self) -> None:
        """
        Rotate TLS cipher suites to avoid detection patterns.
        
        This method cycles through different cipher suites to create
        variation in the TLS handshake fingerprint.
        """
        if not hasattr(self.cloudscraper, 'user_agent'):
            return
        
        user_agent = self.cloudscraper.user_agent
        if not hasattr(user_agent, 'cipherSuite'):
            return
        
        # Get available cipher suites for current browser
        browser_name = getattr(user_agent, 'browser', 'chrome')
        
        try:
            # Get cipher suites from cached data
            available_ciphers = user_agent.get_browser_ciphers(browser_name)
            
            if available_ciphers and len(available_ciphers) > 1:
                # Rotate through cipher suites
                self._cipher_rotation_count += 1
                cipher_index = self._cipher_rotation_count % len(available_ciphers)
                
                # Use a subset of ciphers to create variation
                num_ciphers = min(8, len(available_ciphers))
                start_index = cipher_index % (len(available_ciphers) - num_ciphers + 1)
                selected_ciphers = available_ciphers[start_index:start_index + num_ciphers]
                
                new_cipher_suite = ':'.join(selected_ciphers)
                
                if new_cipher_suite != self.cloudscraper.cipherSuite:
                    self.cloudscraper.cipherSuite = new_cipher_suite
                    
                    # Update the HTTPS adapter with new cipher suite
                    from . import CipherSuiteAdapter
                    self.cloudscraper.mount(
                        'https://',
                        CipherSuiteAdapter(
                            cipherSuite=self.cloudscraper.cipherSuite,
                            ecdhCurve=self.cloudscraper.ecdhCurve,
                            server_hostname=self.cloudscraper.server_hostname,
                            source_address=self.cloudscraper.source_address,
                            ssl_context=self.cloudscraper.ssl_context
                        )
                    )
                    
                    if self.cloudscraper.debug:
                        logger.debug(
                            f'Rotated TLS cipher suite (rotation #{self._cipher_rotation_count})'
                        )
        
        except Exception as e:
            if self.cloudscraper.debug:
                logger.debug(f'TLS cipher rotation failed: {e}')
