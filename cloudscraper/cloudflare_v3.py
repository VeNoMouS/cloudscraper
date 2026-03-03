# -*- coding: utf-8 -*-
"""
cloudscraper.cloudflare_v3
==========================

This module contains the CloudflareV3 challenge handler for JavaScript VM challenges.

Classes:
    - CloudflareV3: Handler for Cloudflare v3 JavaScript VM challenges
"""

from __future__ import annotations

import json
import logging
import random
import re
import time
from collections import OrderedDict
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Dict, Optional

from urllib.parse import urlparse

from .base import ChallengeHandler
from .constants import (
    CLOUDFLARE_CHALLENGE_STATUS_CODES,
    DEFAULT_REQUEST_DELAY
)
from .exceptions import (
    CloudflareIUAMError,
    CloudflareSolveError,
    CloudflareChallengeError,
    CloudflareCaptchaError
)
from .interpreters import JavaScriptInterpreter

if TYPE_CHECKING:
    from requests import Response


logger = logging.getLogger(__name__)


# Pre-compiled regex patterns
_RE_V3_CHALLENGE = re.compile(
    r'cpo\.src\s*=\s*[\'"]/cdn-cgi/challenge-platform/\S+orchestrate/jsch/v3',
    re.M | re.S
)
_RE_V3_CTX = re.compile(r'window\._cf_chl_ctx\s*=', re.M | re.S)
_RE_V3_FORM = re.compile(
    r'<form[^>]*id="challenge-form"[^>]*action="[^"]*__cf_chl_rt_tk=',
    re.M | re.S
)
_RE_CHALLENGE_CTX = re.compile(r'window\._cf_chl_ctx\s*=\s*({.*?});', re.DOTALL)
_RE_CHALLENGE_OPT = re.compile(r'window\._cf_chl_opt\s*=\s*({.*?});', re.DOTALL)
_RE_FORM_ACTION = re.compile(r'<form[^>]*id="challenge-form"[^>]*action="([^"]+)"', re.DOTALL)
_RE_VM_SCRIPT = re.compile(r'<script[^>]*>\s*(.*?window\._cf_chl_enter.*?)</script>', re.DOTALL)
_RE_R_TOKEN = re.compile(r'name="r" value="([^"]+)"')
_RE_INPUT_FIELDS = re.compile(r'<input[^>]*name="([^"]+)"[^>]*value="([^"]*)"')


class CloudflareV3(ChallengeHandler):
    """
    Handler for Cloudflare v3 JavaScript VM challenges.
    """
    
    def __init__(self, cloudscraper: Any, delay: Optional[float] = None) -> None:
        super().__init__(cloudscraper, delay)
        self.delay = delay or getattr(cloudscraper, 'delay', None) or random.uniform(1.0, 5.0)
    
    def is_challenge(self, resp: Response) -> bool:
        try:
            return (
                resp.headers.get('Server', '').startswith('cloudflare')
                and resp.status_code in CLOUDFLARE_CHALLENGE_STATUS_CODES
                and (
                    _RE_V3_CHALLENGE.search(resp.text)
                    or _RE_V3_CTX.search(resp.text)
                    or _RE_V3_FORM.search(resp.text)
                )
            )
        except AttributeError:
            logger.debug("Error checking v3 challenge: %s", getattr(resp, 'status_code', 'unknown'))
        return False
    
    def handle_challenge(self, resp: Response, **kwargs: Any) -> Response:
        try:
            if getattr(self.cloudscraper, 'debug', False):
                logger.debug('Handling Cloudflare v3 JavaScript VM challenge.')
            
            challenge_info = self._extract_v3_challenge_data(resp)
            time.sleep(self.delay)
            
            url_parsed = urlparse(resp.url)
            challenge_answer = self._execute_vm_challenge(challenge_info, url_parsed.netloc)
            payload = self._generate_v3_payload(challenge_info, resp, challenge_answer)
            
            challenge_url = challenge_info['form_action']
            if not challenge_url.startswith('http'):
                challenge_url = f"{url_parsed.scheme}://{url_parsed.netloc}{challenge_url}"
            
            cloudflare_kwargs = deepcopy(kwargs)
            cloudflare_kwargs['allow_redirects'] = False
            cloudflare_kwargs['headers'] = cloudflare_kwargs.get('headers', {})
            cloudflare_kwargs['headers'].update({
                'Origin': f'{url_parsed.scheme}://{url_parsed.netloc}',
                'Referer': resp.url,
                'Content-Type': 'application/x-www-form-urlencoded'
            })
            
            challenge_response = self.cloudscraper.request(
                'POST', challenge_url, data=payload, **cloudflare_kwargs
            )
            
            if challenge_response.status_code == 403:
                raise CloudflareSolveError("Failed to solve Cloudflare v3 challenge")
            
            return challenge_response
            
        except CloudflareChallengeError:
            raise
        except Exception as e:
            logger.error("Error handling Cloudflare v3 challenge: %s", str(e))
            raise CloudflareChallengeError(f"Error handling Cloudflare v3 challenge: {e}")
    
    def _extract_v3_challenge_data(self, resp: Response) -> Dict[str, Any]:
        try:
            ctx_match = _RE_CHALLENGE_CTX.search(resp.text)
            ctx_data = {}
            if ctx_match:
                try:
                    ctx_data = json.loads(ctx_match.group(1))
                except json.JSONDecodeError:
                    pass
            
            opt_match = _RE_CHALLENGE_OPT.search(resp.text)
            opt_data = {}
            if opt_match:
                try:
                    opt_data = json.loads(opt_match.group(1))
                except json.JSONDecodeError:
                    pass
            
            form_match = _RE_FORM_ACTION.search(resp.text)
            if not form_match:
                raise CloudflareChallengeError("Could not find Cloudflare v3 challenge form")
            
            vm_match = _RE_VM_SCRIPT.search(resp.text)
            
            return {
                'ctx_data': ctx_data,
                'opt_data': opt_data,
                'form_action': form_match.group(1),
                'vm_script': vm_match.group(1) if vm_match else None
            }
            
        except CloudflareChallengeError:
            raise
        except Exception as e:
            logger.error("Error extracting Cloudflare v3 challenge data: %s", str(e))
            raise CloudflareChallengeError(f"Error extracting Cloudflare v3 challenge data: {e}")
    
    def _execute_vm_challenge(self, challenge_data: Dict[str, Any], domain: str) -> str:
        try:
            if not challenge_data.get('vm_script'):
                return self._generate_fallback_answer(challenge_data)
            
            vm_script = challenge_data['vm_script']
            
            js_context = f"""
            var window = {{
                location: {{ 
                    href: 'https://{domain}/',
                    hostname: '{domain}',
                    protocol: 'https:',
                    pathname: '/'
                }},
                navigator: {{
                    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    platform: 'Win32',
                    language: 'en-US'
                }},
                document: {{
                    getElementById: function(id) {{
                        return {{ value: '', style: {{}} }};
                    }},
                    createElement: function(tag) {{
                        return {{ 
                            firstChild: {{ href: 'https://{domain}/' }},
                            style: {{}}
                        }};
                    }}
                }},
                _cf_chl_ctx: {json.dumps(challenge_data.get('ctx_data', {}))},
                _cf_chl_opt: {json.dumps(challenge_data.get('opt_data', {}))},
                _cf_chl_enter: function() {{ return true; }}
            }};
            
            var document = window.document;
            var location = window.location;
            var navigator = window.navigator;
            
            {vm_script}
            
            if (typeof window._cf_chl_answer !== 'undefined') {{
                window._cf_chl_answer;
            }} else if (typeof _cf_chl_answer !== 'undefined') {{
                _cf_chl_answer;
            }} else {{
                Math.random().toString(36).substring(2, 15);
            }}
            """
            
            try:
                interpreter = getattr(self.cloudscraper, 'interpreter', 'js2py')
                result = JavaScriptInterpreter.dynamicImport(interpreter).eval(js_context, domain)
                
                if result is not None:
                    return str(result)
            except Exception as js_error:
                logger.warning("JavaScript execution failed: %s, using fallback", str(js_error))
            
            return self._generate_fallback_answer(challenge_data)
            
        except Exception as e:
            logger.error("Error executing v3 VM challenge: %s", str(e))
            return self._generate_fallback_answer(challenge_data)
    
    def _generate_fallback_answer(self, challenge_data: Dict[str, Any]) -> str:
        ctx_data = challenge_data.get('ctx_data', {})
        opt_data = challenge_data.get('opt_data', {})
        
        if 'chlPageData' in opt_data:
            page_data = opt_data['chlPageData']
            return str(hash(page_data) % 1000000)
        elif 'cvId' in ctx_data:
            cv_id = ctx_data['cvId']
            return str(hash(cv_id) % 1000000)
        else:
            return str(random.randint(100000, 999999))
    
    def _generate_v3_payload(
        self, 
        challenge_data: Dict[str, Any], 
        resp: Response, 
        challenge_answer: str
    ) -> OrderedDict:
        try:
            r_match = _RE_R_TOKEN.search(resp.text)
            if not r_match:
                raise CloudflareChallengeError("Could not find 'r' token")
            
            form_fields = {}
            for field_match in _RE_INPUT_FIELDS.finditer(resp.text):
                field_name, field_value = field_match.groups()
                if field_name not in ['jschl_answer']:
                    form_fields[field_name] = field_value
            
            payload = OrderedDict()
            payload['r'] = r_match.group(1)
            payload['jschl_answer'] = challenge_answer
            
            for field_name, field_value in form_fields.items():
                if field_name not in payload:
                    payload[field_name] = field_value
            
            return payload
            
        except Exception as e:
            logger.error("Error generating v3 challenge payload: %s", str(e))
            raise CloudflareChallengeError(f"Error generating v3 challenge payload: {e}")
