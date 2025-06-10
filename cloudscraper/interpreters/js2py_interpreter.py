from __future__ import absolute_import

import re
import js2py
import logging

from ..exceptions import CloudflareSolveError
from . import JavaScriptInterpreter

# ------------------------------------------------------------------------------- #


class ChallengeInterpreter(JavaScriptInterpreter):

    def __init__(self):
        super(ChallengeInterpreter, self).__init__('js2py')
        # Disable pyimport to prevent sys variable conflicts
        js2py.disable_pyimport()
        self.js_engine = js2py.EvalJs()

    # ------------------------------------------------------------------------------- #

    def eval(self, body, domain):
        try:
            # Extract the challenge script
            js_challenge = re.search(
                r"setTimeout\(function\(\){\s+(var s,t,o,p,b,r,e,a,k,i,n,g,f.+?\r?\n[\s\S]+?a\.value =.+?)\r?\n",
                body,
                re.DOTALL
            )
            
            if not js_challenge:
                js_challenge = re.search(
                    r"setTimeout\(function\(\){\s+(var (?:s,t,o,p,b,r,e|t,r,a,n,s),a,c,k,e,d.+?\r?\n[\s\S]+?a\.value =.+?)\r?\n",
                    body,
                    re.DOTALL
                )
                
            if not js_challenge:
                raise CloudflareSolveError("Unable to find Cloudflare challenge script")
                
            js_challenge = js_challenge.group(1)
            
            # Make the challenge script executable in a JS context
            challenge = js_challenge
            
            # Remove DOM manipulation code that js2py can't handle
            challenge = re.sub(r"document\.getElementById\(.*?\)", "{ value: 0 }", challenge)
            challenge = re.sub(r"document\.createElement\(.*?\)", "{ firstChild: { href: 'https://" + domain + "/' } }", challenge)
            challenge = re.sub(r"\.innerHTML", ".innerHTML = ''", challenge)
            challenge = re.sub(r"\.value", ".value", challenge)
            challenge = re.sub(r"\.submit\(\)", "", challenge)
            
            # Add domain info for the challenge
            challenge = "var location = { href: 'https://" + domain + "/' };\n" + challenge
            
            # Add necessary globals to prevent variable conflicts
            self.js_engine.execute('''
                var window = this;
                var global = this;
                var self = this;
                if (typeof console === 'undefined') {
                    var console = {
                        log: function() {},
                        warn: function() {},
                        error: function() {}
                    };
                }
            ''')

            # Execute the challenge in js2py
            self.js_engine.execute(challenge)

            # Extract the answer from the JS context
            if hasattr(self.js_engine, 'a') and hasattr(self.js_engine.a, 'value'):
                return self.js_engine.a.value

            raise CloudflareSolveError("Failed to extract answer from Cloudflare challenge")
            
        except Exception as e:
            logging.error(f"Error solving Cloudflare challenge: {str(e)}")
            raise CloudflareSolveError(f"Error solving Cloudflare challenge: {str(e)}")


# ------------------------------------------------------------------------------- #

ChallengeInterpreter()
