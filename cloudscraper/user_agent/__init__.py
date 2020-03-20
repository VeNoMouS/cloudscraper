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

    def loadHeaders(self, user_agents, user_agent_version):
        if user_agents.get(self.browser).get('releases').get(user_agent_version).get('headers'):
            self.headers = user_agents.get(self.browser).get('releases').get(user_agent_version).get('headers')
        else:
            self.headers = user_agents.get(self.browser).get('default_headers')

    # ------------------------------------------------------------------------------- #

    def filterAgents(self, releases):
        filtered = {}

        for release in releases:
            if self.mobile and releases[release]['User-Agent']['mobile']:
                filtered[release] = filtered.get(release, []) + releases[release]['User-Agent']['mobile']

            if self.desktop and releases[release]['User-Agent']['desktop']:
                filtered[release] = filtered.get(release, []) + releases[release]['User-Agent']['desktop']

        return filtered

    # ------------------------------------------------------------------------------- #

    def tryMatchCustom(self, user_agents):
        for browser in user_agents:
            for release in user_agents[browser]['releases']:
                for platform in ['mobile', 'desktop']:
                    if re.search(re.escape(self.custom), ' '.join(user_agents[browser]['releases'][release]['User-Agent'][platform])):
                        self.browser = browser
                        self.loadHeaders(user_agents, release)
                        self.headers['User-Agent'] = self.custom
                        self.cipherSuite = user_agents[self.browser].get('cipherSuite', [])
                        return True
        return False

    # ------------------------------------------------------------------------------- #

    def loadUserAgent(self, *args, **kwargs):
        self.browser = kwargs.pop('browser', None)

        if isinstance(self.browser, dict):
            self.custom = self.browser.get('custom', None)
            self.desktop = self.browser.get('desktop', True)
            self.mobile = self.browser.get('mobile', True)
            self.browser = self.browser.get('browser', None)
        else:
            self.custom = kwargs.pop('custom', None)
            self.desktop = kwargs.pop('desktop', True)
            self.mobile = kwargs.pop('mobile', True)

        if not self.desktop and not self.mobile:
            sys.tracebacklimit = 0
            raise RuntimeError("Sorry you can't have mobile and desktop disabled at the same time.")

        with open(os.path.join(os.path.dirname(__file__), 'browsers.json'), 'r') as fp:
            user_agents = json.load(
                fp,
                object_pairs_hook=OrderedDict
            )

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
            if self.browser and not user_agents.get(self.browser):
                sys.tracebacklimit = 0
                raise RuntimeError('Sorry "{}" browser User-Agent was not found.'.format(self.browser))

            if not self.browser:
                self.browser = random.SystemRandom().choice(list(user_agents))

            self.cipherSuite = user_agents.get(self.browser).get('cipherSuite', [])

            filteredAgents = self.filterAgents(user_agents.get(self.browser).get('releases'))

            user_agent_version = random.SystemRandom().choice(list(filteredAgents))

            self.loadHeaders(user_agents, user_agent_version)

            self.headers['User-Agent'] = random.SystemRandom().choice(filteredAgents[user_agent_version])

        if not kwargs.get('allow_brotli', False) and 'br' in self.headers['Accept-Encoding']:
            self.headers['Accept-Encoding'] = ','.join([
                encoding for encoding in self.headers['Accept-Encoding'].split(',') if encoding.strip() != 'br'
            ]).strip()
