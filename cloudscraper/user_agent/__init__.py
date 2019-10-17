import json
import os
import random
import sys

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

    def loadUserAgent(self, *args, **kwargs):
        self.browser = kwargs.pop('browser', None)

        if isinstance(self.browser, dict):
            self.desktop = self.browser.get('desktop', True)
            self.mobile = self.browser.get('mobile', True)
            self.browser = self.browser.get('browser', None)
        else:
            self.desktop = kwargs.pop('desktop', True)
            self.mobile = kwargs.pop('mobile', True)

        if not self.desktop and not self.mobile:
            sys.tracebacklimit = 0
            raise RuntimeError("Sorry you can't have mobile and desktop disabled at the same time.")

        user_agents = json.load(
            open(os.path.join(os.path.dirname(__file__), 'browsers.json'), 'r'),
            object_pairs_hook=OrderedDict
        )

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

        if not kwargs.get('allow_brotli', False):
            if 'br' in self.headers['Accept-Encoding']:
                self.headers['Accept-Encoding'] = ','.join([encoding for encoding in self.headers['Accept-Encoding'].split(',') if encoding.strip() != 'br']).strip()
