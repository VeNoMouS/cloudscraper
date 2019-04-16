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

        js = re.sub(r"a\.value = ((.+).toFixed\(10\))?", r"\1", js)
        js = re.sub(r'(e\s=\sfunction\(s\)\s{.*?};)', '', js, flags=re.DOTALL | re.MULTILINE)
        js = re.sub(r"\s{3,}[a-z](?: = |\.).+", "", js).replace("t.length", str(len(domain)))

        js = js.replace('; 121', '')

        # Strip characters that could be used to exit the string context
        # These characters are not currently used in Cloudflare's arithmetic snippet
        js = re.sub(r"[\n\\']", "", js)

        if 'toFixed' not in js:
            raise ValueError("Error parsing Cloudflare IUAM Javascript challenge. {}".format(BUG_REPORT))

        try:
            jsEnv = """
            var t = "{domain}";
            var g = String.fromCharCode;

            o = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";
            e = function(s) {{
                s += "==".slice(2 - (s.length & 3));
                var bm, r = "", r1, r2, i = 0;
                for (; i < s.length;) {{
                    bm = o.indexOf(s.charAt(i++)) << 18 | o.indexOf(s.charAt(i++)) << 12 | (r1 = o.indexOf(s.charAt(i++))) << 6 | (r2 = o.indexOf(s.charAt(i++)));
                    r += r1 === 64 ? g(bm >> 16 & 255) : r2 === 64 ? g(bm >> 16 & 255, bm >> 8 & 255) : g(bm >> 16 & 255, bm >> 8 & 255, bm & 255);
                }}
                return r;
            }};

            function italics (str) {{ return "<i>" + this + "</i>"; }};
            var document = {{
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
            innerHTML = innerHTML.group(2).replace("'", r"\'") if innerHTML else ""
            
            return self.interrupter.solveJS(jsEnv.format(domain=domain, innerHTML=innerHTML), js)
        
        except Exception :
            logging.error("Error executing Cloudflare IUAM Javascript. {}".format(BUG_REPORT))
            raise
        pass
