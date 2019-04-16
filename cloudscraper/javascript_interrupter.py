
import re
import sys
import logging


##########################################################################################################################################################

BUG_REPORT = 'Cloudflare may have changed their technique, or there may be a bug in the script.'

##########################################################################################################################################################


class JavaScript_Interrupter():
    def __init__(self, interrupter='js2py'):
        self.interrupter = None
        self.loadInterrupter(interrupter)
           
    ##########################################################################################################################################################
    
    def loadInterrupter(self, interrupter):
        interrupters = ['js2py', 'nodejs']
        
        if interrupter not in interrupters:
            sys.tracebacklimit = None if sys.version_info[0] == 3 else 0
            raise ValueError(
                'Unknown interrupter "{}", please select one of the following interrupters [ {} ]'.format(
                    interrupter,
                    ', '.join(interrupters)
                )
            )
        
        try:
            mod = __import__('cloudscraper.{}_interrupter'.format(interrupter), fromlist=[interrupter])
            self.interrupter = getattr(mod, '{}_interrupter'.format(interrupter))()
        except (ImportError, AttributeError) as e:
            Exception('Unable to load {} interrupter'.format(interrupter))
            
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
            
            return self.interrupter.solveJS(
                re.sub(r'\s{2,}', ' ', jsEnv.format(domain=domain, innerHTML=innerHTML), flags=re.MULTILINE | re.DOTALL),
                js
            )
        
        except Exception :
            logging.error("Error executing Cloudflare IUAM Javascript. {}".format(BUG_REPORT))
            raise
        pass