import re
import sys
import base64
import logging
import subprocess

##########################################################################################################################################################

BUG_REPORT = 'Cloudflare may have changed their technique, or there may be a bug in the script.'

##########################################################################################################################################################

class nodejs():

    ##########################################################################################################################################################
    
    def solveJS(self, jsEnv, js):
        try:
            js = "var atob = function(str) {return Buffer.from(str, 'base64').toString('binary');}; var injection = atob('%s'); " \
                 "console.log(require('vm').runInNewContext(injection, Object.create(null), {timeout: 5000}));" % base64.b64encode('{}{}'.format(jsEnv, js))
            
            return subprocess.check_output(["node", "-e", js]).strip()
        
        except OSError as e:
            if e.errno == 2:
                raise EnvironmentError(
                    "Missing Node.js runtime. Node is required and must be in the PATH (check with `node -v`). Your Node binary may be called `nodejs` rather than `node`, " \
                    "in which case you may need to run `apt-get install nodejs-legacy` on some Debian-based systems. (Please read the cfscrape" \
                    " README's Dependencies section: https://github.com/VeNoMouS/cloudscraper#dependencies."
                )
            raise
        except Exception:
            logging.error("Error executing Cloudflare IUAM Javascript. %s" % BUG_REPORT)
            raise
        
        pass 

    ##########################################################################################################################################################
    