# -*- coding: utf-8 -*-
"""
cloudscraper.base
=================

This module contains the abstract base class for Cloudflare challenge handlers.

Classes:
    - ChallengeHandler: Abstract base class for all challenge handlers
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from requests import Response


class ChallengeHandler(ABC):
    """
    Abstract base class for Cloudflare challenge handlers.
    
    All challenge handlers (v1, v2, v3, Turnstile) should inherit from this class
    and implement the required methods.
    
    Attributes:
        cloudscraper: Reference to the parent CloudScraper instance
        delay: Delay in seconds before solving the challenge
    """
    
    def __init__(self, cloudscraper: Any, delay: Optional[float] = None) -> None:
        """
        Initialize the challenge handler.
        
        Args:
            cloudscraper: Reference to the parent CloudScraper instance
            delay: Optional delay override in seconds
        """
        self.cloudscraper = cloudscraper
        self.delay = delay or getattr(cloudscraper, 'delay', None)
    
    @abstractmethod
    def is_challenge(self, resp: Response) -> bool:
        """
        Check if the response contains a challenge.
        
        Args:
            resp: The HTTP response to check
            
        Returns:
            True if the response contains a challenge, False otherwise
        """
        pass
    
    @abstractmethod
    def handle_challenge(self, resp: Response, **kwargs: Any) -> Response:
        """
        Handle and solve the challenge.
        
        Args:
            resp: The HTTP response containing the challenge
            **kwargs: Additional arguments for the challenge solver
            
        Returns:
            The response after successfully solving the challenge
        """
        pass
    
    def _extract_form_action(self, resp: Response, pattern: str) -> Optional[str]:
        """
        Extract the form action URL from the challenge page.
        
        Args:
            resp: The HTTP response containing the challenge form
            pattern: Regex pattern to match the form action
            
        Returns:
            The extracted form action URL, or None if not found
        """
        import re
        match = re.search(pattern, resp.text, re.M | re.DOTALL)
        if match:
            return match.group(1) if match.groups() else match.group(0)
        return None
    
    def _extract_input_fields(self, resp: Response, pattern: str) -> Dict[str, str]:
        """
        Extract input field names and values from the challenge form.
        
        Args:
            resp: The HTTP response containing the challenge form
            pattern: Regex pattern to match input fields
            
        Returns:
            Dictionary of field names to        import re
 values
        """
        from collections import OrderedDict
        
        payload = OrderedDict()
        for field_match in re.finditer(pattern, resp.text, re.M | re.DOTALL):
            field_name, field_value = field_match.groups()
            if field_name in ['r', 'jschl_vc', 'pass']:
                payload[field_name] = field_value
        return payload
