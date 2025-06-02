import json
import os
import random
import re
import sys
import ssl

from collections import OrderedDict

# ------------------------------------------------------------------------------- #


class User_Agent():

    # ------------------------------------------------------------------------------- #

    def __init__(self, *args, **kwargs):
        self.headers = None
        self.cipherSuite = []
        self.loadUserAgent(*args, **kwargs)

    # ------------------------------------------------------------------------------- #

    def filterAgents(self, user_agents):
        filtered = {}

        if self.mobile:
            if self.platform in user_agents['mobile'] and user_agents['mobile'][self.platform]:
                filtered.update(user_agents['mobile'][self.platform])

        if self.desktop:
            if self.platform in user_agents['desktop'] and user_agents['desktop'][self.platform]:
                filtered.update(user_agents['desktop'][self.platform])

        return filtered

    # ------------------------------------------------------------------------------- #

    def tryMatchCustom(self, user_agents):
        for device_type in user_agents['user_agents']:
            for platform in user_agents['user_agents'][device_type]:
                for browser in user_agents['user_agents'][device_type][platform]:
                    if re.search(re.escape(self.custom), ' '.join(user_agents['user_agents'][device_type][platform][browser])):
                        self.headers = user_agents['headers'][browser]
                        self.headers['User-Agent'] = self.custom
                        self.cipherSuite = user_agents['cipherSuite'][browser]
                        return True
        return False

    # ------------------------------------------------------------------------------- #

    def loadUserAgent(self, *args, **kwargs):
        self.browser = kwargs.pop('browser', None)

        self.platforms = ['linux', 'windows', 'darwin', 'android', 'ios']
        self.browsers = ['chrome', 'firefox']

        if isinstance(self.browser, dict):
            self.custom = self.browser.get('custom', None)
            self.platform = self.browser.get('platform', None)
            self.desktop = self.browser.get('desktop', True)
            self.mobile = self.browser.get('mobile', True)
            self.browser = self.browser.get('browser', None)
        else:
            self.custom = kwargs.pop('custom', None)
            self.platform = kwargs.pop('platform', None)
            self.desktop = kwargs.pop('desktop', True)
            self.mobile = kwargs.pop('mobile', True)

        if not self.desktop and not self.mobile:
            sys.tracebacklimit = 0
            raise RuntimeError("Sorry you can't have mobile and desktop disabled at the same time.")

        try:
            # Try to load from the normal location
            browsers_json_path = os.path.join(os.path.dirname(__file__), 'browsers.json')
            with open(browsers_json_path, 'r') as fp:
                user_agents = json.load(
                    fp,
                    object_pairs_hook=OrderedDict
                )
        except (FileNotFoundError, IOError):
            # Fallback for executable environments
            try:
                # Try alternative paths for executables
                import sys
                if getattr(sys, 'frozen', False):
                    # Running in a PyInstaller bundle
                    bundle_dir = sys._MEIPASS
                    browsers_json_path = os.path.join(bundle_dir, 'cloudscraper', 'user_agent', 'browsers.json')
                else:
                    # Try current directory
                    browsers_json_path = os.path.join(os.getcwd(), 'browsers.json')

                with open(browsers_json_path, 'r') as fp:
                    user_agents = json.load(
                        fp,
                        object_pairs_hook=OrderedDict
                    )
            except (FileNotFoundError, IOError):
                # Ultimate fallback - use comprehensive hardcoded user agents
                user_agents = {
                    "headers": {
                        "chrome": {
                            "User-Agent": None,
                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                            "Accept-Language": "en-US,en;q=0.9",
                            "Accept-Encoding": "gzip, deflate, br"
                        },
                        "firefox": {
                            "User-Agent": None,
                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                            "Accept-Language": "en-US,en;q=0.5",
                            "Accept-Encoding": "gzip, deflate, br"
                        }
                    },
                    "cipherSuite": {
                        "chrome": [
                            "TLS_AES_128_GCM_SHA256",
                            "TLS_AES_256_GCM_SHA384",
                            "ECDHE-ECDSA-AES128-GCM-SHA256",
                            "ECDHE-RSA-AES128-GCM-SHA256",
                            "ECDHE-ECDSA-AES256-GCM-SHA384",
                            "ECDHE-RSA-AES256-GCM-SHA384"
                        ],
                        "firefox": [
                            "TLS_AES_128_GCM_SHA256",
                            "TLS_CHACHA20_POLY1305_SHA256",
                            "TLS_AES_256_GCM_SHA384",
                            "ECDHE-ECDSA-AES128-GCM-SHA256",
                            "ECDHE-RSA-AES128-GCM-SHA256",
                            "ECDHE-ECDSA-AES256-GCM-SHA384"
                        ]
                    },
                    "user_agents": {
                        "desktop": {
                            "windows": {
                                "chrome": [
                                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                                    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                                ],
                                "firefox": [
                                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
                                    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:120.0) Gecko/20100101 Firefox/120.0"
                                ]
                            },
                            "linux": {
                                "chrome": [
                                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                                    "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                                ],
                                "firefox": [
                                    "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
                                    "Mozilla/5.0 (X11; Linux i686; rv:120.0) Gecko/20100101 Firefox/120.0"
                                ]
                            },
                            "darwin": {
                                "chrome": [
                                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                                ],
                                "firefox": [
                                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0"
                                ]
                            }
                        },
                        "mobile": {
                            "android": {
                                "chrome": [
                                    "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
                                    "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
                                ],
                                "firefox": [
                                    "Mozilla/5.0 (Mobile; rv:120.0) Gecko/120.0 Firefox/120.0"
                                ]
                            },
                            "ios": {
                                "chrome": [
                                    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.0.0 Mobile/15E148 Safari/604.1"
                                ],
                                "firefox": [
                                    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/120.0.0.0 Mobile/15E148 Safari/605.1.15"
                                ]
                            }
                        }
                    }
                }

        if self.custom:
            if not self.tryMatchCustom(user_agents):
                self.cipherSuite = [
                    ssl._DEFAULT_CIPHERS,
                    '!AES128-SHA',
                    '!ECDHE-RSA-AES256-SHA',
                ]
                self.headers = OrderedDict([
                    ('User-Agent', self.custom),
                    ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'),
                    ('Accept-Language', 'en-US,en;q=0.9'),
                    ('Accept-Encoding', 'gzip, deflate, br')
                ])
        else:
            if self.browser and self.browser not in self.browsers:
                sys.tracebacklimit = 0
                raise RuntimeError(f'Sorry "{self.browser}" browser is not valid, valid browsers are [{", ".join(self.browsers)}].')

            if not self.platform:
                self.platform = random.SystemRandom().choice(self.platforms)

            if self.platform not in self.platforms:
                sys.tracebacklimit = 0
                raise RuntimeError(f'Sorry the platform "{self.platform}" is not valid, valid platforms are [{", ".join(self.platforms)}]')

            filteredAgents = self.filterAgents(user_agents['user_agents'])

            if not self.browser:
                # has to be at least one in there...
                while not filteredAgents.get(self.browser):
                    self.browser = random.SystemRandom().choice(list(filteredAgents.keys()))

            if not filteredAgents[self.browser]:
                sys.tracebacklimit = 0
                raise RuntimeError(f'Sorry "{self.browser}" browser was not found with a platform of "{self.platform}".')

            self.cipherSuite = user_agents['cipherSuite'][self.browser]
            self.headers = user_agents['headers'][self.browser]

            self.headers['User-Agent'] = random.SystemRandom().choice(filteredAgents[self.browser])

        if not kwargs.get('allow_brotli', False) and 'br' in self.headers['Accept-Encoding']:
            self.headers['Accept-Encoding'] = ','.join([
                encoding for encoding in self.headers['Accept-Encoding'].split(',') if encoding.strip() != 'br'
            ]).strip()
