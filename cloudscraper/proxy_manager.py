import random
import logging
import time
from collections import defaultdict

# ------------------------------------------------------------------------------- #


class ProxyManager:
    """
    A class to manage and rotate proxies for CloudScraper
    """

    def __init__(self, proxies=None, proxy_rotation_strategy='sequential', ban_time=300):
        """
        Initialize the proxy manager
        
        :param proxies: List of proxy URLs or dict mapping URL schemes to proxy URLs
        :param proxy_rotation_strategy: Strategy for rotating proxies ('sequential', 'random', or 'smart')
        :param ban_time: Time in seconds to ban a proxy after a failure (for 'smart' strategy)
        """
        self.proxies = []
        self.current_index = 0
        self.rotation_strategy = proxy_rotation_strategy
        self.ban_time = ban_time
        self.banned_proxies = {}
        self.proxy_stats = defaultdict(lambda: {'success': 0, 'failure': 0, 'last_used': 0})
        
        # Process the provided proxies
        if proxies:
            if isinstance(proxies, list):
                self.proxies = proxies
            elif isinstance(proxies, dict):
                # Extract unique proxy URLs from the dict
                for scheme, proxy in proxies.items():
                    if proxy and proxy not in self.proxies:
                        self.proxies.append(proxy)
            elif isinstance(proxies, str):
                self.proxies = [proxies]
                
        logging.debug(f"ProxyManager initialized with {len(self.proxies)} proxies using '{proxy_rotation_strategy}' strategy")

    # ------------------------------------------------------------------------------- #

    def get_proxy(self):
        """
        Get the next proxy according to the rotation strategy
        
        :return: A proxy URL or dict mapping URL schemes to proxy URLs
        """
        if not self.proxies:
            return None
            
        # Filter out banned proxies
        available_proxies = [p for p in self.proxies if p not in self.banned_proxies or 
                            time.time() - self.banned_proxies[p] > self.ban_time]
        
        if not available_proxies:
            logging.warning("All proxies are currently banned. Using the least recently banned one.")
            # Use the least recently banned proxy
            proxy = min(self.banned_proxies.items(), key=lambda x: x[1])[0]
            # Reset its ban time
            self.banned_proxies.pop(proxy)
            return self._format_proxy(proxy)
        
        # Choose a proxy based on the strategy
        if self.rotation_strategy == 'random':
            proxy = random.choice(available_proxies)
        elif self.rotation_strategy == 'smart':
            # Choose the proxy with the best success rate
            proxy = max(available_proxies, 
                        key=lambda p: (self.proxy_stats[p]['success'] / 
                                      (self.proxy_stats[p]['success'] + self.proxy_stats[p]['failure'] + 0.1)))
        else:  # sequential
            if self.current_index >= len(available_proxies):
                self.current_index = 0
            proxy = available_proxies[self.current_index]
            self.current_index += 1
            
        # Update last used time
        self.proxy_stats[proxy]['last_used'] = time.time()
        
        return self._format_proxy(proxy)

    # ------------------------------------------------------------------------------- #

    def _format_proxy(self, proxy):
        """
        Format the proxy as a dict for requests
        
        :param proxy: Proxy URL
        :return: Dict mapping URL schemes to proxy URLs
        """
        if proxy.startswith('http://') or proxy.startswith('https://'):
            return {'http': proxy, 'https': proxy}
        else:
            return {'http': f'http://{proxy}', 'https': f'http://{proxy}'}

    # ------------------------------------------------------------------------------- #

    def report_success(self, proxy):
        """
        Report a successful request with the proxy
        
        :param proxy: The proxy that was used
        """
        if isinstance(proxy, dict):
            # Extract the proxy URL from the dict
            proxy_url = proxy.get('https') or proxy.get('http')
        else:
            proxy_url = proxy
            
        if proxy_url:
            self.proxy_stats[proxy_url]['success'] += 1
            if proxy_url in self.banned_proxies:
                del self.banned_proxies[proxy_url]

    # ------------------------------------------------------------------------------- #

    def report_failure(self, proxy):
        """
        Report a failed request with the proxy
        
        :param proxy: The proxy that was used
        """
        if isinstance(proxy, dict):
            # Extract the proxy URL from the dict
            proxy_url = proxy.get('https') or proxy.get('http')
        else:
            proxy_url = proxy
            
        if proxy_url:
            self.proxy_stats[proxy_url]['failure'] += 1
            self.banned_proxies[proxy_url] = time.time()

    # ------------------------------------------------------------------------------- #

    def add_proxy(self, proxy):
        """
        Add a new proxy to the pool
        
        :param proxy: Proxy URL to add
        """
        if proxy not in self.proxies:
            self.proxies.append(proxy)
            logging.debug(f"Added proxy: {proxy}")

    # ------------------------------------------------------------------------------- #

    def remove_proxy(self, proxy):
        """
        Remove a proxy from the pool
        
        :param proxy: Proxy URL to remove
        """
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            if proxy in self.banned_proxies:
                del self.banned_proxies[proxy]
            if proxy in self.proxy_stats:
                del self.proxy_stats[proxy]
            logging.debug(f"Removed proxy: {proxy}")

    # ------------------------------------------------------------------------------- #

    def get_stats(self):
        """
        Get statistics about proxy usage
        
        :return: Dict with proxy statistics
        """
        return {
            'total_proxies': len(self.proxies),
            'available_proxies': len([p for p in self.proxies if p not in self.banned_proxies or 
                                     time.time() - self.banned_proxies[p] > self.ban_time]),
            'banned_proxies': len(self.banned_proxies),
            'proxy_stats': dict(self.proxy_stats)
        }
