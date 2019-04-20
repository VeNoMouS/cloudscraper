import base64
import logging
import subprocess

from . import JavaScriptInterpreter

##########################################################################################################################################################

BUG_REPORT = 'Cloudflare may have changed their technique, or there may be a bug in the script.'

##########################################################################################################################################################


class ChallengeInterpreter(JavaScriptInterpreter):

    def __init__(self):
        super(ChallengeInterpreter, self).__init__('nodejs')

    def eval(self, jsEnv, js):
        try:
            js = 'var atob = function(str) {return Buffer.from(str, "base64").toString("binary");};' \
                 'var challenge = atob("%s");' \
                 'var context = {atob: atob};' \
                 'var options = {filename: "iuam-challenge.js", timeout: 4000};' \
                 'var answer = require("vm").runInNewContext(challenge, context, options);' \
                 'process.stdout.write(String(answer));' \
                 % base64.b64encode('{}{}'.format(jsEnv, js).encode('UTF-8')).decode('ascii')

            return subprocess.check_output(['node', '-e', js])

        except OSError as e:
            if e.errno == 2:
                raise EnvironmentError(
                    'Missing Node.js runtime. Node is required and must be in the PATH (check with `node -v`). Your Node binary may be called `nodejs` rather than `node`, '
                    'in which case you may need to run `apt-get install nodejs-legacy` on some Debian-based systems. (Please read the cloudscraper'
                    ' README\'s Dependencies section: https://github.com/VeNoMouS/cloudscraper#dependencies.'
                )
            raise
        except Exception:
            logging.error('Error executing Cloudflare IUAM Javascript. %s' % BUG_REPORT)
            raise

        pass


ChallengeInterpreter()
