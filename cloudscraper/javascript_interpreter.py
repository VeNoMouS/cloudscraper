
import re
import sys
import logging

##########################################################################################################################################################

BUG_REPORT = 'Cloudflare may have changed their technique, or there may be a bug in the script.'

##########################################################################################################################################################


class JavaScript_Interpreter():
    def __init__(self, interpreter='js2py'):
        self.interpreter = None
        self.loadinterpreter(interpreter)
           
    ##########################################################################################################################################################
    
    def loadinterpreter(self, interpreter):
        interpreters = ['js2py', 'nodejs']
        
        if interpreter not in interpreters:
            sys.tracebacklimit = None if sys.version_info[0] == 3 else 0
            raise ValueError(
                'Unknown interpreter "{}", please select one of the following interpreters [ {} ]'.format(
                    interpreter,
                    ', '.join(interpreters)
                )
            )
        
        try:
            mod = __import__('cloudscraper.interpreters.{}'.format(interpreter), fromlist=[interpreter])
            self.interpreter = getattr(mod, '{}'.format(interpreter))()
        except (ImportError, AttributeError) as e:
            Exception('Unable to load {} interpreter'.format(interpreter))
            
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
            
            return self.interpreter.solveJS(
                re.sub(r'\s{2,}', ' ', jsEnv.format(domain=domain, innerHTML=innerHTML), flags=re.MULTILINE | re.DOTALL),
                js
            )
        
        except Exception :
            logging.error("Error executing Cloudflare IUAM Javascript. {}".format(BUG_REPORT))
            raise
        pass