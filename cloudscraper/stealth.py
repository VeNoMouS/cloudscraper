import random
import time
from collections import OrderedDict

# ------------------------------------------------------------------------------- #


class StealthMode:
    """
    Stealth mode implementation for avoiding bot detection
    """

    def __init__(self, cloudscraper, min_delay=0.5, max_delay=2.0,
                 human_like_delays=True, randomize_headers=True, browser_quirks=True,
                 simulate_viewport=True, behavioral_patterns=True):

        self.cloudscraper = cloudscraper
        self.request_count = 0
        self.last_request_time = 0
        self.session_start = time.time()

        # Basic config
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.human_like_delays = human_like_delays
        self.randomize_headers = randomize_headers
        self.browser_quirks = browser_quirks
        self.simulate_viewport = simulate_viewport
        self.behavioral_patterns = behavioral_patterns

        # Session tracking
        self.reading_wpm = random.uniform(200, 400)
        self.visit_times = []

        # Screen setup - pick common resolutions
        resolutions = [(1920, 1080), (1366, 768), (1536, 864), (1440, 900), (1280, 720)]
        self.screen_w, self.screen_h = random.choice(resolutions)
        self.viewport_w = self.screen_w - random.randint(0, 100)
        self.viewport_h = self.screen_h - random.randint(100, 200)

        # Browser header patterns - copied from real browsers
        self.browser_headers = {
            'chrome': {
                'order': ['Host', 'Connection', 'sec-ch-ua', 'sec-ch-ua-mobile', 'sec-ch-ua-platform',
                          'User-Agent', 'Accept', 'Sec-Fetch-Site', 'Sec-Fetch-Mode', 'Sec-Fetch-User',
                          'Sec-Fetch-Dest', 'Referer', 'Accept-Encoding', 'Accept-Language', 'Cookie'],
                'defaults': {
                    'sec-ch-ua': '"Google Chrome";v="120", "Not_A Brand";v="8", "Chromium";v="120"',
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
                'defaults': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Upgrade-Insecure-Requests': '1',
                    'Connection': 'keep-alive'
                }
            }
        }

    # ------------------------------------------------------------------------------- #

    def apply_stealth_techniques(self, method, url, **kwargs):
        """Apply stealth stuff to make requests look human"""

        # Wait a bit between requests
        if self.human_like_delays:
            self._wait_like_human(url)

        # Add screen size info
        if self.simulate_viewport:
            kwargs = self._add_screen_info(kwargs)

        # Mix up headers
        if self.randomize_headers:
            kwargs = self._randomize_headers(kwargs)

        # Make headers look like real browser
        if self.browser_quirks:
            kwargs = self._fix_header_order(kwargs)

        # Add some behavioral stuff
        if self.behavioral_patterns:
            kwargs = self._add_behavior_headers(method, url, kwargs)

        # Keep track of requests
        self.request_count += 1
        self.last_request_time = time.time()
        self.visit_times.append(time.time())

        return kwargs

    # ------------------------------------------------------------------------------- #

    def _wait_like_human(self, url=None):
        """Wait between requests like a real person would"""
        if self.request_count == 0:
            return  # First request, no delay

        # Basic random delay
        delay = random.uniform(self.min_delay, self.max_delay)

        # Sometimes people read stuff
        if random.random() < 0.3:
            delay += random.uniform(2, 8)

        # Sometimes people get distracted
        if random.random() < 0.05:
            delay += random.uniform(10, 30)

        # Same domain = faster (people know where stuff is)
        if url and hasattr(self, '_last_domain'):
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            if domain == self._last_domain:
                delay *= 0.7
            self._last_domain = domain
        elif url:
            from urllib.parse import urlparse
            self._last_domain = urlparse(url).netloc

        # Get faster over time (familiarity)
        session_time = time.time() - self.session_start
        if session_time > 300:  # 5 minutes
            speed_up = min(0.2, (session_time - 300) / 3600)
            delay *= (1 - speed_up)

        # Don't wait forever
        delay = min(delay, 45.0)

        if delay >= 0.1:
            time.sleep(delay)

    # ------------------------------------------------------------------------------- #

    # ------------------------------------------------------------------------------- #

    def _add_screen_info(self, kwargs):
        """Add screen size and viewport info"""
        headers = kwargs.get('headers', {})

        # Viewport size
        headers['Viewport-Width'] = str(self.viewport_w)
        headers['Viewport-Height'] = str(self.viewport_h)

        # Screen size (sometimes)
        if random.random() < 0.5:
            headers['Screen-Width'] = str(self.screen_w)
            headers['Screen-Height'] = str(self.screen_h)

        # Pixel ratio
        ratios = [1.0, 1.25, 1.5, 2.0]
        headers['Device-Pixel-Ratio'] = str(random.choice(ratios))

        # Timezone
        timezones = [-480, -420, -360, -300, -240, -180, 0, 60, 120, 180, 240, 300, 360, 480, 540]
        headers['Timezone-Offset'] = str(random.choice(timezones))

        kwargs['headers'] = headers
        return kwargs

    # ------------------------------------------------------------------------------- #

    def _add_behavior_headers(self, method, url, kwargs):
        """Add some behavioral stuff to headers"""
        headers = kwargs.get('headers', {})

        # How long on previous page
        if len(self.visit_times) > 1:
            time_on_page = self.visit_times[-1] - self.visit_times[-2]
            if time_on_page > 0:
                headers['X-Focus-Time'] = str(int(time_on_page * 1000))

        # POST requests = forms
        if method.upper() == 'POST':
            form_time = random.uniform(5, 30)
            headers['X-Form-Time'] = str(int(form_time * 1000))

            if 'data' in kwargs or 'json' in kwargs:
                typing_time = random.uniform(0.1, 0.3) * 50
                headers['X-Typing-Time'] = str(int(typing_time * 1000))

        # How many pages visited
        headers['X-Session-Depth'] = str(len(self.visit_times))

        # Tab focused?
        focus_chance = max(0.7, 1.0 - (len(self.visit_times) * 0.05))
        headers['X-Tab-Focus'] = 'true' if random.random() < focus_chance else 'false'

        # Different page types
        if url:
            from urllib.parse import urlparse
            path = urlparse(url).path.lower()

            if any(word in path for word in ['login', 'signin', 'auth']):
                headers['X-Page-Type'] = 'auth'
            elif any(word in path for word in ['search', 'query']):
                headers['X-Page-Type'] = 'search'
            elif any(word in path for word in ['product', 'item', 'detail']):
                headers['X-Page-Type'] = 'product'

        kwargs['headers'] = headers
        return kwargs

    # ------------------------------------------------------------------------------- #

    def _randomize_headers(self, kwargs):
        """Mix up headers so they look different each time"""
        headers = kwargs.get('headers', {})

        # Accept header variations
        if 'Accept' not in headers:
            accept_options = [
                'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'
            ]
            headers['Accept'] = random.choice(accept_options)

        # Language stuff
        if 'Accept-Language' not in headers:
            langs = [
                'en-US,en;q=0.9',
                'en-US,en;q=0.8',
                'en-GB,en;q=0.9,en-US;q=0.8',
                'en-CA,en;q=0.9,en-US;q=0.8',
                'en-AU,en;q=0.9,en-US;q=0.8'
            ]
            headers['Accept-Language'] = random.choice(langs)

        # Encoding
        if 'Accept-Encoding' not in headers:
            encodings = ['gzip, deflate, br', 'gzip, deflate', 'gzip, deflate, br, zstd']
            headers['Accept-Encoding'] = random.choice(encodings)

        # Do Not Track (some people have this)
        if random.random() < 0.4:
            headers['DNT'] = '1'

        # Cache stuff
        if random.random() < 0.3:
            cache_opts = ['max-age=0', 'no-cache', 'max-age=0, must-revalidate']
            headers['Cache-Control'] = random.choice(cache_opts)

        if random.random() < 0.2:
            headers['Pragma'] = 'no-cache'

        # Connection type
        if 'Connection' not in headers:
            headers['Connection'] = random.choice(['keep-alive', 'close'])

        kwargs['headers'] = headers
        return kwargs

    # ------------------------------------------------------------------------------- #

    def _fix_header_order(self, kwargs):
        """Put headers in the right order like real browsers do"""
        user_agent = kwargs.get('headers', {}).get('User-Agent', '')

        # Figure out browser type
        if 'Firefox/' in user_agent:
            browser = 'firefox'
        else:
            browser = 'chrome'  # default

        headers = kwargs.get('headers', {})

        # Add browser-specific headers
        for header, value in self.browser_headers[browser]['defaults'].items():
            if header not in headers:
                headers[header] = value

        # Put headers in correct order
        if headers:
            ordered = OrderedDict()
            # Add in browser order first
            for header in self.browser_headers[browser]['order']:
                if header in headers:
                    ordered[header] = headers[header]
            # Add any leftover headers
            for header, value in headers.items():
                if header not in ordered:
                    ordered[header] = value

            kwargs['headers'] = ordered

        return kwargs

    # ------------------------------------------------------------------------------- #

    def set_delay_range(self, min_delay, max_delay):
        """Change delay settings"""
        self.min_delay = min_delay
        self.max_delay = max_delay

    def calc_reading_time(self, content_length):
        """How long would it take to read this much text?"""
        words = content_length / 5  # rough estimate
        reading_time = (words / self.reading_wpm) * 60
        reading_time *= random.uniform(0.8, 1.2)  # add some variation
        return max(1.0, min(reading_time, 30.0))



    def get_human_timing_signature(self):
        """Get stats about this session"""
        now = time.time()
        duration = now - self.session_start

        return {
            'session_duration': duration,
            'request_count': self.request_count,
            'avg_request_interval': duration / max(1, self.request_count),
            'reading_speed': self.reading_wpm,
            'viewport_size': f"{self.viewport_w}x{self.viewport_h}",
            'screen_size': f"{self.screen_w}x{self.screen_h}"
        }

    def reset_session(self):
        """Start fresh session"""
        self.session_start = time.time()
        self.request_count = 0
        self.visit_times = []

        # New random characteristics
        self.reading_wpm = random.uniform(200, 400)

        # Sometimes change screen size
        if random.random() < 0.1:
            resolutions = [(1920, 1080), (1366, 768), (1536, 864), (1440, 900), (1280, 720)]
            self.screen_w, self.screen_h = random.choice(resolutions)
            self.viewport_w = self.screen_w - random.randint(0, 100)
            self.viewport_h = self.screen_h - random.randint(100, 200)
