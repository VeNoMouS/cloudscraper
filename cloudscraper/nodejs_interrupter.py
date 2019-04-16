import re
import sys
import subprocess

##########################################################################################################################################################

BUG_REPORT = 'Cloudflare may have changed their technique, or there may be a bug in the script.'

##########################################################################################################################################################

class nodejs_interrupter():

    ##########################################################################################################################################################
    
    def solveJS(self, jsEnv, js):
        try:
            js = re.sub(r"[\n\\']", "", '{}{}'.format(jsEnv, js))
            js = "console.log(require('vm').runInNewContext('%s', Object.create(null), {timeout: 5000}));" % js
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
    