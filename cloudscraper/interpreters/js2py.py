from __future__ import absolute_import

import js2py
import logging
import base64

from . import JavaScriptInterpreter

from .jsunfuck import jsunfuck


class ChallengeInterpreter(JavaScriptInterpreter):

    def __init__(self):
        super(ChallengeInterpreter, self).__init__('js2py')

    def eval(self, jsEnv, js):
        if js2py.eval_js('(+(+!+[]+[+!+[]]+(!![]+[])[!+[]+!+[]+!+[]]+[!+[]+!+[]]+[+[]])+[])[+!+[]]') == '1':
            logging.warning('WARNING - Please upgrade your js2py https://github.com/PiotrDabkowski/Js2Py, applying work around for the meantime.')
            js = jsunfuck(js)

        def atob(s):
            return base64.b64decode('{}'.format(s)).decode('utf-8')

        js2py.disable_pyimport()
        context = js2py.EvalJs({'atob': atob})
        result = context.eval('{}{}'.format(jsEnv, js))

        return result


ChallengeInterpreter()
