import js2py
import logging

from .jsunfuck import jsunfuck

##########################################################################################################################################################


class js2py_interpreter():

    ##########################################################################################################################################################

    def solveJS(self, jsEnv, js):
        if js2py.eval_js('(+(+!+[]+[+!+[]]+(!![]+[])[!+[]+!+[]+!+[]]+[!+[]+!+[]]+[+[]])+[])[+!+[]]') == '1':
            logging.warning('WARNING - Please upgrade your js2py https://github.com/PiotrDabkowski/Js2Py, applying work around for the meantime.')
            js = jsunfuck(js)

        def atob(s):
            return base64.b64decode('{}'.format(s)).decode('utf-8')

        js2py.disable_pyimport()
        context = js2py.EvalJs({'atob': atob})
        result = context.eval('{}{}'.format(jsEnv, js))

        return result

    ##########################################################################################################################################################
