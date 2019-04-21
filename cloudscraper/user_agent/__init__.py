import os
import json
import random
import logging

from collections import OrderedDict
from pprint import pprint

class User_Agent():
    def __init__(self, *args, **kwargs):
        self.headers = None
        self.loadUserAgent(*args, **kwargs)
    
    def loadUserAgent(self, *args, **kwargs):
        browser = kwargs.pop('browser', 'chrome')
        
        user_agents = json.load(
            open(os.path.join(os.path.dirname(__file__), 'browsers.json'), 'r'),
            object_pairs_hook=OrderedDict
        )

        if not user_agents.get(browser):
            logging.error('Sorry {} User-Agent was not found.'.format(browser))
            raise
        
        user_agent = random.choice(user_agents.get(browser))
        self.headers= user_agent.get('headers')
        self.headers['User-Agent'] = random.choice(user_agent.get('User-Agent'))
        if not kwargs.get('allow_br', False):
            self.headers['Accept-Encoding'] = self.headers['Accept-Encoding'].replace(', br', '')
        
            
        