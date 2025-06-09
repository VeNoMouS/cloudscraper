import random
import time
import logging
from collections import OrderedDict

# ------------------------------------------------------------------------------- #


class StealthMode:
    """
    A class to implement stealth techniques to avoid detection as a scraper
    """

    def __init__(self, cloudscraper):
        """
        Initialize the stealth mode
        
        :param cloudscraper: The CloudScraper instance
        """
        self.cloudscraper = cloudscraper
        self.request_count = 0
        self.last_request_time = 0
        self.human_like_delays = True
        self.randomize_headers = True
        self.browser_quirks = True
        
        # Default human-like delay ranges (in seconds) - More reasonable defaults
        self.min_delay = 0.5
        self.max_delay = 2.0
        
        # Browser quirks settings
        self.quirks = {
            'chrome': {
                'order': ['Host', 'Connection', 'sec-ch-ua', 'sec-ch-ua-mobile', 'sec-ch-ua-platform', 
                          'User-Agent', 'Accept', 'Sec-Fetch-Site', 'Sec-Fetch-Mode', 'Sec-Fetch-User', 
                          'Sec-Fetch-Dest', 'Referer', 'Accept-Encoding', 'Accept-Language', 'Cookie'],
                'headers': {
                    'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-User': '?1',
                    'Sec-Fetch-Dest': 'document',
                    'Accept-Language': 'en-US,en;q=0.9'
                }
            },
            'firefox': {
                'order': ['Host', 'User-Agent', 'Accept', 'Accept-Language', 'Accept-Encoding', 
                          'Connection', 'Upgrade-Insecure-Requests', 'Referer', 'Cookie'],
                'headers': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Upgrade-Insecure-Requests': '1',
                    'Connection': 'keep-alive'
                }
            }
        }

    # ------------------------------------------------------------------------------- #

    def apply_stealth_techniques(self, method, url, **kwargs):
        """
        Apply stealth techniques to the request
        
        :param method: HTTP method
        :param url: URL to request
        :param kwargs: Additional arguments for the request
        :return: Modified kwargs
        """
        # Apply human-like delays between requests
        if self.human_like_delays:
            self._apply_human_like_delay()
            
        # Randomize headers to look more like a browser
        if self.randomize_headers:
            kwargs = self._randomize_headers(kwargs)
            
        # Apply browser-specific quirks
        if self.browser_quirks:
            kwargs = self._apply_browser_quirks(kwargs)
            
        # Track request count and time
        self.request_count += 1
        self.last_request_time = time.time()
        
        return kwargs

    # ------------------------------------------------------------------------------- #

    def _apply_human_like_delay(self):
        """
        Add a random delay between requests to mimic human behavior
        """
        # Skip delay for the first request
        if self.request_count > 0:
            # Calculate a random delay
            delay = random.uniform(self.min_delay, self.max_delay)

            # Add some randomness to make it look more human, but cap it
            if random.random() < 0.1:  # 10% chance of a longer pause
                delay *= 1.5  # Reduced from 2x to 1.5x

            # Cap maximum delay to prevent excessive waits
            delay = min(delay, 10.0)  # Never wait more than 10 seconds

            # Skip delay if it would be too short to matter
            if delay >= 0.1:
                logging.debug(f"Applying human-like delay of {delay:.2f} seconds")
                time.sleep(delay)

    # ------------------------------------------------------------------------------- #

    def _randomize_headers(self, kwargs):
        """
        Randomize headers to avoid fingerprinting
        
        :param kwargs: Request kwargs
        :return: Modified kwargs with randomized headers
        """
        headers = kwargs.get('headers', {})
        
        # Don't modify User-Agent as it's handled by the User_Agent class
        
        # Randomize Accept header slightly (if not already set)
        if 'Accept' not in headers:
            accepts = [
                'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            ]
            headers['Accept'] = random.choice(accepts)
            
        # Randomize Accept-Language (if not already set)
        if 'Accept-Language' not in headers:
            languages = [
                'en-US,en;q=0.9',
                'en-US,en;q=0.8',
                'en-GB,en;q=0.9,en-US;q=0.8',
                'en-CA,en;q=0.9,en-US;q=0.8',
                'en-AU,en;q=0.9,en-US;q=0.8'
            ]
            headers['Accept-Language'] = random.choice(languages)
            
        # Add random DNT (Do Not Track) header
        if random.random() < 0.5:  # 50% chance
            headers['DNT'] = '1'
            
        kwargs['headers'] = headers
        return kwargs

    # ------------------------------------------------------------------------------- #

    def _apply_browser_quirks(self, kwargs):
        """
        Apply browser-specific quirks to make requests look more authentic
        
        :param kwargs: Request kwargs
        :return: Modified kwargs with browser quirks
        """
        # Determine which browser we're mimicking
        user_agent = kwargs.get('headers', {}).get('User-Agent', '')
        browser_type = 'chrome'  # Default
        
        if 'Firefox/' in user_agent:
            browser_type = 'firefox'
        elif 'Chrome/' in user_agent:
            browser_type = 'chrome'
            
        # Apply browser-specific headers
        headers = kwargs.get('headers', {})
        for header, value in self.quirks[browser_type]['headers'].items():
            if header not in headers:
                headers[header] = value
                
        # Reorder headers to match browser's order
        if headers:
            ordered_headers = OrderedDict()
            # First add headers in the browser's preferred order
            for header in self.quirks[browser_type]['order']:
                if header in headers:
                    ordered_headers[header] = headers[header]
            # Then add any remaining headers
            for header, value in headers.items():
                if header not in ordered_headers:
                    ordered_headers[header] = value
                    
            kwargs['headers'] = ordered_headers
            
        return kwargs

    # ------------------------------------------------------------------------------- #

    def set_delay_range(self, min_delay, max_delay):
        """
        Set the range for random delays between requests
        
        :param min_delay: Minimum delay in seconds
        :param max_delay: Maximum delay in seconds
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
        
    # ------------------------------------------------------------------------------- #

    def enable_human_like_delays(self, enabled=True):
        """
        Enable or disable human-like delays between requests
        
        :param enabled: Whether to enable human-like delays
        """
        self.human_like_delays = enabled
        
    # ------------------------------------------------------------------------------- #

    def enable_randomize_headers(self, enabled=True):
        """
        Enable or disable header randomization
        
        :param enabled: Whether to enable header randomization
        """
        self.randomize_headers = enabled
        
    # ------------------------------------------------------------------------------- #

    def enable_browser_quirks(self, enabled=True):
        """
        Enable or disable browser quirks
        
        :param enabled: Whether to enable browser quirks
        """
        self.browser_quirks = enabled
