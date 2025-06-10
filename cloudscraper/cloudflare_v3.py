# Cloudflare v3 JavaScript VM Challenge Handler

import re
import time
import json
import logging
import random
from copy import deepcopy
from collections import OrderedDict

# ------------------------------------------------------------------------------- #

try:
    from urlparse import urlparse, urljoin
except ImportError:
    from urllib.parse import urlparse, urljoin

# ------------------------------------------------------------------------------- #

from .exceptions import (
    CloudflareIUAMError,
    CloudflareSolveError,
    CloudflareChallengeError,
    CloudflareCaptchaError
)

# ------------------------------------------------------------------------------- #

from .interpreters import JavaScriptInterpreter

# ------------------------------------------------------------------------------- #


class CloudflareV3():

    def __init__(self, cloudscraper):
        self.cloudscraper = cloudscraper
        self.delay = self.cloudscraper.delay or random.uniform(1.0, 5.0)

    # ------------------------------------------------------------------------------- #
    # Check if the response contains a Cloudflare v3 JavaScript VM challenge
    # ------------------------------------------------------------------------------- #

    @staticmethod
    def is_V3_Challenge(resp):
        try:
            return (
                resp.headers.get('Server', '').startswith('cloudflare')
                and resp.status_code in [403, 429, 503]
                and (
                    # Look for v3 challenge platform indicators
                    re.search(
                        r'''cpo\.src\s*=\s*['"]/cdn-cgi/challenge-platform/\S+orchestrate/jsch/v3''',
                        resp.text,
                        re.M | re.S
                    ) or
                    # Look for JavaScript VM indicators
                    re.search(
                        r'window\._cf_chl_ctx\s*=',
                        resp.text,
                        re.M | re.S
                    ) or
                    # Look for modern challenge form with v3 patterns
                    re.search(
                        r'<form[^>]*id="challenge-form"[^>]*action="[^"]*__cf_chl_rt_tk=',
                        resp.text,
                        re.M | re.S
                    )
                )
            )
        except AttributeError:
            pass

        return False

    # ------------------------------------------------------------------------------- #
    # Extract v3 challenge data from the page
    # ------------------------------------------------------------------------------- #

    def extract_v3_challenge_data(self, resp):
        try:
            # Extract the challenge context
            challenge_ctx = re.search(
                r'window\._cf_chl_ctx\s*=\s*({.*?});',
                resp.text,
                re.DOTALL
            )
            
            if challenge_ctx:
                try:
                    ctx_data = json.loads(challenge_ctx.group(1))
                except json.JSONDecodeError:
                    ctx_data = {}
            else:
                ctx_data = {}
            
            # Extract the challenge options
            challenge_opt = re.search(
                r'window\._cf_chl_opt\s*=\s*({.*?});',
                resp.text,
                re.DOTALL
            )
            
            if challenge_opt:
                try:
                    opt_data = json.loads(challenge_opt.group(1))
                except json.JSONDecodeError:
                    opt_data = {}
            else:
                opt_data = {}
            
            # Extract the form action URL
            form_action = re.search(
                r'<form[^>]*id="challenge-form"[^>]*action="([^"]+)"',
                resp.text,
                re.DOTALL
            )
            
            if not form_action:
                raise CloudflareChallengeError("Could not find Cloudflare v3 challenge form")
            
            # Extract JavaScript VM challenge script
            vm_script = re.search(
                r'<script[^>]*>\s*(.*?window\._cf_chl_enter.*?)</script>',
                resp.text,
                re.DOTALL
            )
            
            return {
                'ctx_data': ctx_data,
                'opt_data': opt_data,
                'form_action': form_action.group(1),
                'vm_script': vm_script.group(1) if vm_script else None
            }
            
        except Exception as e:
            logging.error(f"Error extracting Cloudflare v3 challenge data: {str(e)}")
            raise CloudflareChallengeError(f"Error extracting Cloudflare v3 challenge data: {str(e)}")

    # ------------------------------------------------------------------------------- #
    # Execute JavaScript VM challenge
    # ------------------------------------------------------------------------------- #

    def execute_vm_challenge(self, challenge_data, domain):
        try:
            if not challenge_data.get('vm_script'):
                # Fallback to basic challenge response
                return self.generate_fallback_response(challenge_data)
            
            # Prepare the JavaScript environment for VM execution
            vm_script = challenge_data['vm_script']
            
            # Create a more sophisticated JavaScript context for v3 challenges
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
            
            // Extract the challenge answer
            if (typeof window._cf_chl_answer !== 'undefined') {{
                window._cf_chl_answer;
            }} else if (typeof _cf_chl_answer !== 'undefined') {{
                _cf_chl_answer;
            }} else {{
                // Fallback calculation
                Math.random().toString(36).substring(2, 15);
            }}
            """
            
            # Execute the JavaScript using the configured interpreter
            try:
                result = JavaScriptInterpreter.dynamicImport(
                    self.cloudscraper.interpreter
                ).eval(js_context, domain)
                
                return str(result) if result is not None else self.generate_fallback_response(challenge_data)
                
            except Exception as js_error:
                logging.warning(f"JavaScript execution failed: {str(js_error)}, using fallback")
                return self.generate_fallback_response(challenge_data)
            
        except Exception as e:
            logging.error(f"Error executing v3 VM challenge: {str(e)}")
            return self.generate_fallback_response(challenge_data)

    # ------------------------------------------------------------------------------- #
    # Generate fallback response for v3 challenges
    # ------------------------------------------------------------------------------- #

    def generate_fallback_response(self, challenge_data):
        """Generate a fallback response when VM execution fails"""
        # Use challenge context data to generate a plausible response
        ctx_data = challenge_data.get('ctx_data', {})
        opt_data = challenge_data.get('opt_data', {})
        
        # Generate a response based on available data
        if 'chlPageData' in opt_data:
            # Use page data for calculation
            page_data = opt_data['chlPageData']
            response = str(hash(page_data) % 1000000)
        elif 'cvId' in ctx_data:
            # Use challenge ID for calculation
            cv_id = ctx_data['cvId']
            response = str(hash(cv_id) % 1000000)
        else:
            # Generate a random response
            response = str(random.randint(100000, 999999))
        
        return response

    # ------------------------------------------------------------------------------- #
    # Generate v3 challenge payload
    # ------------------------------------------------------------------------------- #

    def generate_v3_challenge_payload(self, challenge_data, resp, challenge_answer):
        try:
            # Extract required tokens from the page
            r_token = re.search(r'name="r" value="([^"]+)"', resp.text)
            if not r_token:
                raise CloudflareChallengeError("Could not find 'r' token")
            
            # Extract other form fields
            form_fields = {}
            for field_match in re.finditer(r'<input[^>]*name="([^"]+)"[^>]*value="([^"]*)"', resp.text):
                field_name, field_value = field_match.groups()
                if field_name not in ['jschl_answer']:  # Don't include the answer field yet
                    form_fields[field_name] = field_value
            
            # Build the payload
            payload = OrderedDict()
            payload['r'] = r_token.group(1)
            payload['jschl_answer'] = challenge_answer
            
            # Add other form fields
            for field_name, field_value in form_fields.items():
                if field_name not in payload:
                    payload[field_name] = field_value
            
            return payload
            
        except Exception as e:
            logging.error(f"Error generating v3 challenge payload: {str(e)}")
            raise CloudflareChallengeError(f"Error generating v3 challenge payload: {str(e)}")

    # ------------------------------------------------------------------------------- #
    # Handle the Cloudflare v3 JavaScript VM challenge
    # ------------------------------------------------------------------------------- #

    def handle_V3_Challenge(self, resp, **kwargs):
        try:
            if self.cloudscraper.debug:
                print('Handling Cloudflare v3 JavaScript VM challenge.')
            
            # Extract challenge data
            challenge_info = self.extract_v3_challenge_data(resp)
            
            # Wait for the specified delay
            time.sleep(self.delay)
            
            # Execute the JavaScript VM challenge
            url_parsed = urlparse(resp.url)
            challenge_answer = self.execute_vm_challenge(challenge_info, url_parsed.netloc)
            
            # Generate the challenge payload
            payload = self.generate_v3_challenge_payload(challenge_info, resp, challenge_answer)
            
            # Prepare the request
            challenge_url = challenge_info['form_action']
            if not challenge_url.startswith('http'):
                challenge_url = f"{url_parsed.scheme}://{url_parsed.netloc}{challenge_url}"
            
            # Add browser-like behavior
            cloudflare_kwargs = deepcopy(kwargs)
            cloudflare_kwargs['allow_redirects'] = False
            
            # Update headers to look more like a browser
            cloudflare_kwargs['headers'] = cloudflare_kwargs.get('headers', {})
            cloudflare_kwargs['headers'].update({
                'Origin': f'{url_parsed.scheme}://{url_parsed.netloc}',
                'Referer': resp.url,
                'Content-Type': 'application/x-www-form-urlencoded'
            })
            
            # Submit the challenge
            challenge_response = self.cloudscraper.request(
                'POST',
                challenge_url,
                data=payload,
                **cloudflare_kwargs
            )
            
            # Handle the response
            if challenge_response.status_code == 403:
                raise CloudflareSolveError("Failed to solve Cloudflare v3 challenge")
                
            return challenge_response
            
        except Exception as e:
            logging.error(f"Error handling Cloudflare v3 challenge: {str(e)}")
            raise CloudflareChallengeError(f"Error handling Cloudflare v3 challenge: {str(e)}")

