
import re
import sys
import logging

from os import listdir
from os.path import isfile, join, dirname, realpath

##########################################################################################################################################################

BUG_REPORT = 'Cloudflare may have changed their technique, or there may be a bug in the script.'

##########################################################################################################################################################


class JavaScript_Interpreter():
    def __init__(self, interpreter='js2py'):
        self.interpreter = None
        self.interpreters = [
            f.replace('_interpreter.py', '') for f in listdir(join(dirname(realpath(__file__)), 'interpreters'))
            if f.endswith('_interpreter.py') and
            isfile(join(join(dirname(realpath(__file__)), 'interpreters'), f))
        ]
        self.loadInterpreter(interpreter)
           
    ##########################################################################################################################################################
    
    def loadInterpreter(self, interpreter):
        interpreter = 'js2py' if interpreter == 'None' else interpreter
        
        if interpreter not in self.interpreters:
            sys.tracebacklimit = None if sys.version_info[0] == 3 else 0
            raise ValueError(
                'Unknown interpreter "{}", please select one of the following interpreters [ {} ]'.format(
                    interpreter,
                    ', '.join(self.interpreters)
                )
            )
        
        try:
            interpreter = '{}_interpreter'.format(interpreter)
            mod = __import__('cloudscraper.interpreters.{}'.format(interpreter), fromlist=[interpreter])
            self.interpreter = getattr(mod, '{}'.format(interpreter))()
        except (ImportError, AttributeError) as e:
            logging.error('Unable to load {} interpreter'.format(interpreter))
            raise
            
    ##########################################################################################################################################################
    
    def solveJS(self, body, domain):
        try:
            js = re.search(
                r"setTimeout\(function\(\){\s+(var s,t,o,p,b,r,e,a,k,i,n,g,f.+?\r?\n[\s\S]+?a\.value =.+?)\r?\n",
                body
            ).group(1)
        except Exception:
            raise ValueError("Unable to identify Cloudflare IUAM Javascript on website. {}".format(BUG_REPORT))

        js = re.sub(r'\s{2,}', ' ', js, flags=re.MULTILINE | re.DOTALL)
        js = js.replace('\'; 121\'', '')
        js += '\na.value;';

        if 'toFixed' not in js:
            raise ValueError("Error parsing Cloudflare IUAM Javascript challenge. {}".format(BUG_REPORT))

        try:
            jsEnv = """
            function italics (str) {{ return "<i>" + this + "</i>"; }};
            var document = {{
                createElement: function () {{
                    return {{ firstChild: {{ href: "http://{domain}/" }} }}
                }},
                getElementById: function () {{
                    return {{"innerHTML": "{innerHTML}"}};
                }}
            }};
            
            """

            innerHTML = re.search(
                '<div(?: [^<>]*)? id="([^<>]*?)">([^<>]*?)<\/div>',
                body,
                re.MULTILINE | re.DOTALL
            )
            innerHTML = innerHTML.group(2) if innerHTML else ""
            
            result = self.interpreter.solveJS(
                re.sub(r'\s{2,}', ' ', jsEnv.format(domain=domain, innerHTML=innerHTML), flags=re.MULTILINE | re.DOTALL),
                js
            )
        except:
            logging.error("Error extracting Cloudflare IUAM Javascript.".format(BUG_REPORT))
            raise
        
        try:
            float(result)
        except Exception :
            logging.error("Error executing Cloudflare IUAM Javascript. {}".format(BUG_REPORT))
            raise
        
        return result