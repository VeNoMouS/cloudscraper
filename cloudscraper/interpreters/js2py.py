from __future__ import absolute_import

import js2py
import logging
import base64

from . import JavaScriptInterpreter

from .encapsulated import template
from .jsunfuck import jsunfuck

# ------------------------------------------------------------------------------- #


class ChallengeInterpreter(JavaScriptInterpreter):

    # ------------------------------------------------------------------------------- #

    def __init__(self):
        super(ChallengeInterpreter, self).__init__('js2py')

    # ------------------------------------------------------------------------------- #

    def eval(self, body, domain):
        try:
            jsPayload = template(body, domain)

            # Check js2py version compatibility
            try:
                test_result = js2py.eval_js('(+(+!+[]+[+!+[]]+(!![]+[])[!+[]+!+[]+!+[]]+[!+[]+!+[]]+[+[]])+[])[+!+[]]')
                if test_result == '1':
                    logging.warning('WARNING - Please upgrade your js2py https://github.com/PiotrDabkowski/Js2Py, applying work around for the meantime.')
                    jsPayload = jsunfuck(jsPayload)
            except Exception as version_error:
                if 'bytecode' in str(version_error).lower():
                    logging.warning(f'js2py version compatibility issue detected: {version_error}')
                    logging.warning('Attempting to continue with basic js2py functionality...')
                else:
                    raise version_error

            def atob(s):
                return base64.b64decode('{}'.format(s)).decode('utf-8')

            # Disable pyimport to prevent sys variable conflicts
            js2py.disable_pyimport()

            # Create a clean context with minimal globals to avoid variable conflicts
            context = js2py.EvalJs({'atob': atob})

            # Add necessary globals that might be missing
            context.execute('''
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

            result = context.eval(jsPayload)
            return result

        except Exception as e:
            logging.error(f'js2py evaluation failed: {str(e)}')
            # Try to extract a more specific error message
            if 'sys' in str(e) and 'not associated with a value' in str(e):
                logging.error('js2py sys variable conflict detected. This may be due to a js2py version issue.')
                # Try a fallback approach
                try:
                    # Create a completely isolated context
                    isolated_context = js2py.EvalJs()
                    isolated_context.execute('var atob = function(s) { return ""; };')  # Dummy atob
                    result = isolated_context.eval(jsPayload)
                    return result
                except Exception as fallback_error:
                    logging.error(f'Fallback js2py evaluation also failed: {str(fallback_error)}')
            raise


# ------------------------------------------------------------------------------- #

ChallengeInterpreter()
