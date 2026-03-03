# -*- coding: utf-8 -*-
"""
cloudscraper.session_manager
============================

This module contains the SessionManager class for handling CloudScraper session
health, refresh, and cookie management.

Classes:
    - SessionManager: Manages session lifecycle and health monitoring
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any, Optional

from .constants import (
    DEFAULT_SESSION_REFRESH_INTERVAL,
    DEFAULT_MAX_403_RETRIES,
    DEFAULT_REQUEST_TIMEOUT,
    CLOUDFLARE_COOKIE_NAMES
)

if TYPE_CHECKING:
    from requests import Response, Session


logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages CloudScraper session health, refresh, and cookie handling.
    
    This class is responsible for:
    - Tracking session age and health
    - Automatic session refresh on staleness or 403 errors
    - Cloudflare cookie management
    - 403 error handling and retry logic
    
    Attributes:
        session_start_time: Timestamp when the session was created/refreshed
        request_count: Number of requests made in this session
        last_403_time: Timestamp of the last 403 error
        session_refresh_interval: Seconds before session is considered stale
        auto_refresh_on_403: Whether to automatically refresh on 403 errors
        max_403_retries: Maximum number of 403 retry attempts
    """
    
    def __init__(
        self,
        cloudscraper: Any,
        session_refresh_interval: int = DEFAULT_SESSION_REFRESH_INTERVAL,
        auto_refresh_on_403: bool = True,
        max_403_retries: int = DEFAULT_MAX_403_RETRIES,
        request_timeout: int = DEFAULT_REQUEST_TIMEOUT
    ) -> None:
        """
        Initialize the SessionManager.
        
        Args:
            cloudscraper: Reference to the parent CloudScraper instance
            session_refresh_interval: Seconds before session is considered stale
            auto_refresh_on_403: Whether to automatically refresh on 403 errors
            max_403_retries: Maximum number of 403 retry attempts
            request_timeout: Timeout for requests in seconds
        """
        self.cloudscraper = cloudscraper
        self.session_refresh_interval = session_refresh_interval
        self.auto_refresh_on_403 = auto_refresh_on_403
        self.max_403_retries = max_403_retries
        self.request_timeout = request_timeout
        
        # Initialize session tracking
        self.session_start_time = time.time()
        self.request_count = 0
        self.last_403_time = 0
        self._403_retry_count = 0
        self._in_403_retry = False
    
    def should_refresh(self) -> bool:
        """
        Check if the session should be refreshed.
        
        Returns:
            True if the session should be refreshed, False otherwise
        """
        current_time = time.time()
        session_age = current_time - self.session_start_time
        
        # Refresh if session is older than the configured interval
        if session_age > self.session_refresh_interval:
            return True
        
        # Refresh if we've had recent 403 errors (within last 60 seconds)
        if self.last_403_time > 0 and (current_time - self.last_403_time) < 60:
            return True
        
        return False
    
    def refresh(self, url: str) -> bool:
        """
        Refresh the session by clearing cookies and re-establishing connection.
        
        Args:
            url: The URL to test the refreshed session against
            
        Returns:
            True if refresh was successful, False otherwise
        """
        try:
            if self.cloudscraper.debug:
                logger.debug('Refreshing session due to staleness or 403 errors...')
            
            # Clear existing Cloudflare cookies
            self._clear_cloudflare_cookies()
            
            # Reset session tracking
            self.session_start_time = time.time()
            self.request_count = 0
            
            # Generate new user agent to avoid fingerprint detection
            if hasattr(self.cloudscraper, 'user_agent'):
                self.cloudscraper.user_agent.loadUserAgent()
                self.cloudscraper.headers.update(self.cloudscraper.user_agent.headers)
            
            # Make a simple request to re-establish session
            try:
                from urllib.parse import urlparse
                parsed_url = urlparse(url)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                
                # Make a lightweight request to trigger challenge solving
                test_response = self.cloudscraper.request(
                    'GET',
                    base_url,
                    timeout=self.request_timeout
                )
                
                success = test_response.status_code in [200, 301, 302, 304]
                
                if success and self.cloudscraper.debug:
                    logger.debug('Session refresh successful')
                elif not success and self.cloudscraper.debug:
                    logger.debug(f'Session refresh failed with status: {test_response.status_code}')
                
                return success
                
            except Exception as e:
                if self.cloudscraper.debug:
                    logger.debug(f'Session refresh failed: {e}')
                return False
        
        except Exception as e:
            if self.cloudscraper.debug:
                logger.debug(f'Error during session refresh: {e}')
            return False
    
    def _clear_cloudflare_cookies(self) -> None:
        """
        Clear Cloudflare-specific cookies to force re-authentication.
        """
        for cookie_name in CLOUDFLARE_COOKIE_NAMES:
            # Remove cookies for all domains
            for domain in list(self.cloudscraper.cookies.list_domains()):
                try:
                    self.cloudscraper.cookies.clear(domain, '/', cookie_name)
                except Exception:
                    pass
        
        if self.cloudscraper.debug:
            logger.debug('Cleared Cloudflare cookies for session refresh')
    
    def handle_403(self, response: 'Response', method: str, url: str, *args: Any, **kwargs: Any) -> Optional['Response']:
        """
        Handle 403 errors with automatic session refresh.
        
        Args:
            response: The HTTP response that returned 403
            method: HTTP method
            url: Request URL
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            The response after retry, or None if max retries exceeded
        """
        if not self.auto_refresh_on_403:
            return None
        
        if self._403_retry_count >= self.max_403_retries:
            if self.cloudscraper.debug:
                logger.debug(f'Max 403 retries ({self.max_403_retries}) exceeded')
            return None
        
        self._403_retry_count += 1
        self.last_403_time = time.time()
        
        if self.cloudscraper.debug:
            logger.debug(f'Received 403 error, attempting session refresh (attempt {self._403_retry_count}/{self.max_403_retries})')
        
        # Try to refresh the session and retry the request
        if self.refresh(url):
            if self.cloudscraper.debug:
                logger.debug('Session refreshed successfully, retrying original request...')
            
            # Mark that we're in a retry to prevent retry count reset
            self._in_403_retry = True
            try:
                # Retry the original request
                retry_response = self.cloudscraper.request(method, url, *args, **kwargs)
                
                # If retry was successful, reset retry count
                if retry_response.status_code == 200:
                    self._403_retry_count = 0
                    if self.cloudscraper.debug:
                        logger.debug('403 retry successful, request completed')
                
                return retry_response
            finally:
                # Always clear the retry flag
                self._in_403_retry = False
        else:
            if self.cloudscraper.debug:
                logger.debug('Session refresh failed, returning 403 response')
            return None
    
    def reset_on_success(self, response: 'Response') -> None:
        """
        Reset retry counters on successful request.
        
        Args:
            response: The successful HTTP response
        """
        # Reset solve depth counter if no challenge was detected
        if not response.is_redirect and response.status_code not in [429, 503]:
            # Reset 403 retry count on successful request (only if not in retry mode)
            if response.status_code == 200 and not self._in_403_retry:
                self._403_retry_count = 0
    
    def increment_request_count(self) -> None:
        """Increment the request counter."""
        self.request_count += 1
