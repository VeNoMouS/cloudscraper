import os
import json
import random
import logging

from collections import OrderedDict

##########################################################################################################################################################


class User_Agent():

    ##########################################################################################################################################################

    def __init__(self, *args, **kwargs):
        self.headers = None
        self.loadUserAgent(*args, **kwargs)

    ##########################################################################################################################################################

    def loadUserAgent(self, *args, **kwargs):
        browser = kwargs.pop('browser', None)

        user_agents = json.load(
            open(os.path.join(os.path.dirname(__file__), 'browsers.json'), 'r'),
            object_pairs_hook=OrderedDict
        )

        if browser and not user_agents.get(browser):
            logging.error('Sorry "{}" browser User-Agent was not found.'.format(browser))
            raise

        if not browser:
            browser = random.SystemRandom().choice(list(user_agents))

        user_agent_version = random.SystemRandom().choice(list(user_agents.get(browser).get('releases')))

        if user_agents.get(browser).get('releases').get(user_agent_version).get('headers'):
            self.headers = user_agents.get(browser).get('releases').get(user_agent_version).get('headers')
        else:
            self.headers = user_agents.get(browser).get('default_headers')

        self.headers['User-Agent'] = random.SystemRandom().choice(user_agents.get(browser).get('releases').get(user_agent_version).get('User-Agent'))

        if not kwargs.get('allow_brotli', False):
            if 'br' in self.headers['Accept-Encoding']:
                self.headers['Accept-Encoding'] = ','.join([encoding for encoding in self.headers['Accept-Encoding'].split(',') if encoding.strip() != 'br']).strip()
