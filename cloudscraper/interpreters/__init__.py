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
        if name not in interpreters:
            try:
                __import__('{}.{}'.format(cls.__module__, name))
                if not isinstance(interpreters.get(name), JavaScriptInterpreter):
                    raise ImportError('The interpreter was not initialized.')
            except ImportError:
                logging.error('Unable to load {} interpreter'.format(name))
                raise

        return interpreters[name]

    @abc.abstractmethod
    def eval(self, jsEnv, js):
        pass

    def solveChallenge(self, body, domain):
        try:
            js = re.search(
                r'setTimeout\(function\(\){\s+(var s,t,o,p,b,r,e,a,k,i,n,g,f.+?\r?\n[\s\S]+?a\.value =.+?)\r?\n',
                body
            ).group(1)
        except Exception:
            raise ValueError('Unable to identify Cloudflare IUAM Javascript on website. {}'.format(BUG_REPORT))

        js = re.sub(r'\s{2,}', ' ', js, flags=re.MULTILINE | re.DOTALL).replace('\'; 121\'', '')
        js += '\na.value;'

        jsEnv = '''
            String.prototype.italics=function(str) {{return "<i>" + this + "</i>";}};
            var document = {{
                createElement: function () {{
                    return {{ firstChild: {{ href: "https://{domain}/" }} }}
                }},
                getElementById: function () {{
                    return {{"innerHTML": "{innerHTML}"}};
                }}
            }};
        '''

        try:
            innerHTML = re.search(
                r'<div(?: [^<>]*)? id="([^<>]*?)">([^<>]*?)</div>',
                body,
                re.MULTILINE | re.DOTALL
            )
            innerHTML = innerHTML.group(2) if innerHTML else ''

        except:  # noqa
            logging.error('Error extracting Cloudflare IUAM Javascript. {}'.format(BUG_REPORT))
            raise

        try:
            result = self.eval(
                re.sub(r'\s{2,}', ' ', jsEnv.format(domain=domain, innerHTML=innerHTML), flags=re.MULTILINE | re.DOTALL),
                js
            )

            float(result)
        except Exception:
            logging.error('Error executing Cloudflare IUAM Javascript. {}'.format(BUG_REPORT))
            raise

        return result
