import re
import sys
import logging
import abc

if sys.version_info >= (3, 4):
    ABC = abc.ABC  # noqa
else:
    ABC = abc.ABCMeta('ABC', (), {})

##########################################################################################################################################################

BUG_REPORT = 'Cloudflare may have changed their technique, or there may be a bug in the script.'

##########################################################################################################################################################

interpreters = {}


class JavaScriptInterpreter(ABC):
    @abc.abstractmethod
    def __init__(self, name):
        interpreters[name] = self

    @classmethod
    def dynamicImport(cls, name):
        jsInterpreter = getattr(interpreters, name, None)
        if jsInterpreter is not None:
            return jsInterpreter

        try:
            __import__('cloudscraper.interpreters.{}'.format(name))
            jsInterpreter = interpreters[name]

            if not isinstance(jsInterpreter, JavaScriptInterpreter):
                raise ValueError('{} failed to register properly'.format(name))

            return jsInterpreter
        except (ImportError, KeyError):
            logging.error('Unable to load {} interpreter'.format(name))
            raise

    @abc.abstractmethod
    def eval(self, jsEnv, js):
        pass

    def solveChallenge(self, body, domain):
        try:
            js = re.search(
                r"setTimeout\(function\(\){\s+(var s,t,o,p,b,r,e,a,k,i,n,g,f.+?\r?\n[\s\S]+?a\.value =.+?)\r?\n",
                body
            ).group(1)
        except Exception:
            raise ValueError("Unable to identify Cloudflare IUAM Javascript on website. {}".format(BUG_REPORT))

        js = re.sub(r'\s{2,}', ' ', js, flags=re.MULTILINE | re.DOTALL).replace('\'; 121\'', '')
        js += '\na.value;'

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
                r'<div(?: [^<>]*)? id="([^<>]*?)">([^<>]*?)</div>',
                body,
                re.MULTILINE | re.DOTALL
            )
            innerHTML = innerHTML.group(2) if innerHTML else ""

            result = self.eval(
                re.sub(r'\s{2,}', ' ', jsEnv.format(domain=domain, innerHTML=innerHTML), flags=re.MULTILINE | re.DOTALL),
                js
            )
        except:  # noqa
            logging.error("Error extracting Cloudflare IUAM Javascript.".format(BUG_REPORT))
            raise

        try:
            float(result)
        except Exception:
            logging.error("Error executing Cloudflare IUAM Javascript. {}".format(BUG_REPORT))
            raise

        return result
