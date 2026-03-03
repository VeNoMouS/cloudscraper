# -*- coding: utf-8 -*-
"""
cloudscraper.user_agent
=======================

This module handles user agent generation and management.
"""

from __future__ import annotations

import json
import logging
import os
import random
import ssl
import sys
from collections import OrderedDict
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Module-level cache for browsers data
_browsers_cache: Optional[Dict[str, Any]] = None


class User_Agent:
    """Handles user agent generation and browser fingerprinting."""
    
    def __init__(self, *args: Any, **kwargs: Any):
        self.headers = None
        self.cipherSuite = []
        self.loadUserAgent(*args, **kwargs)
    
    def filterAgents(self, user_agents: Dict[str, Any]) -> Dict[str, Any]:
        filtered = {}
        
        if self.mobile:
            if self.platform in user_agents.get('mobile', {}) and user_agents['mobile'][self.platform]:
                filtered.update(user_agents['mobile'][self.platform])
        
        if self.desktop:
            if self.platform in user_agents.get('desktop', {}) and user_agents['desktop'][self.platform]:
                filtered.update(user_agents['desktop'][self.platform])
        
        return filtered
    
    def tryMatchCustom(self, user_agents: Dict[str, Any]) -> bool:
        import re
        for device_type in user_agents.get('user_agents', {}):
            for platform in user_agents['user_agents'].get(device_type, {}):
                for browser in user_agents['user_agents'][device_type].get(platform, {}):
                    if hasattr(self, 'custom') and self.custom:
                        if re.search(re.escape(self.custom), ' '.join(user_agents['user_agents'][device_type][platform][browser])):
                            self.headers = user_agents['headers'][browser]
                            self.headers['User-Agent'] = self.custom
                            self.cipherSuite = user_agents['cipherSuite'][browser]
                            return True
        return False
    
    def loadUserAgent(self, *args: Any, **kwargs: Any) -> None:
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
        
        # Load browsers data
        user_agents = self._load_browsers_data()
        
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
            
            filteredAgents = self.filterAgents(user_agents.get('user_agents', {}))
            
            if not self.browser:
                while not filteredAgents.get(self.browser):
                    self.browser = random.SystemRandom().choice(list(filteredAgents.keys()))
            
            if not filteredAgents.get(self.browser):
                sys.tracebacklimit = 0
                raise RuntimeError(f'Sorry "{self.browser}" browser was not found with a platform of "{self.platform}".')
            
            self.cipherSuite = user_agents.get('cipherSuite', {}).get(self.browser, [])
            self.headers = user_agents.get('headers', {}).get(self.browser, {}).copy()
            
            if self.headers and filteredAgents.get(self.browser):
                ua_list = filteredAgents[self.browser]
                if ua_list:
                    self.headers['User-Agent'] = random.SystemRandom().choice(ua_list)
        
        # Handle brotli
        if not kwargs.get('allow_brotli', False):
            encoding = self.headers.get('Accept-Encoding', '')
            if 'br' in encoding:
                self.headers['Accept-Encoding'] = ','.join([
                    e.strip() for e in encoding.split(',') if e.strip() != 'br'
                ]).strip()
    
    def _load_browsers_data(self) -> Dict[str, Any]:
        global _browsers_cache
        
        if _browsers_cache is not None:
            return _browsers_cache
        
        try:
            browsers_json_path = os.path.join(os.path.dirname(__file__), 'browsers.json')
            with open(browsers_json_path, 'r') as fp:
                _browsers_cache = json.load(fp, object_pairs_hook=OrderedDict)
                return _browsers_cache
        except (FileNotFoundError, IOError):
            pass
        
        # Try PyInstaller path
        try:
            if getattr(sys, 'frozen', False):
                bundle_dir = sys._MEIPASS
                browsers_json_path = os.path.join(bundle_dir, 'cloudscraper', 'user_agent', 'browsers.json')
                with open(browsers_json_path, 'r') as fp:
                    _browsers_cache = json.load(fp, object_pairs_hook=OrderedDict)
                    return _browsers_cache
        except (FileNotFoundError, IOError, AttributeError):
            pass
        
        # Fallback data
        _browsers_cache = self._get_fallback_data()
        return _browsers_cache
    
    def _get_fallback_data(self) -> Dict[str, Any]:
        return {
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
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                        ],
                        "firefox": [
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
                        ]
                    }
                }
            }
        }
    
    def get_browser_ciphers(self, browser_name: str) -> List[str]:
        """Get cipher suites for a specific browser."""
        data = self._load_browsers_data()
        return data.get('cipherSuite', {}).get(browser_name, [])
