import base64
import subprocess
import sys

from . import JavaScriptInterpreter
from .encapsulated import template

# ------------------------------------------------------------------------------- #


class ChallengeInterpreter(JavaScriptInterpreter):

    # ------------------------------------------------------------------------------- #

    def __init__(self):
        super(ChallengeInterpreter, self).__init__('nodejs')

    # ------------------------------------------------------------------------------- #

    def eval(self, body, domain):
        try:
            js = 'var atob = function(str) {return Buffer.from(str, "base64").toString("binary");};' \
                 'var challenge = atob("%s");' \
                 'var context = {atob: atob};' \
                 'var options = {filename: "iuam-challenge.js", timeout: 4000};' \
                 'var answer = require("vm").runInNewContext(challenge, context, options);' \
                 'process.stdout.write(String(answer));' \
                 % base64.b64encode(template(body, domain).encode('UTF-8')).decode('ascii')

            return subprocess.check_output(['node', '-e', js])

        except OSError as e:
            if e.errno == 2:
                raise EnvironmentError(
                    'Missing Node.js runtime. Node is required and must be in the PATH (check with `node -v`).\n\n'
                    'Your Node binary may be called `nodejs` rather than `node`, '
                    'in which case you may need to run `apt-get install nodejs-legacy` on some Debian-based systems.\n\n'
                    '(Please read the cloudscraper README\'s Dependencies section: '
                    'https://github.com/VeNoMouS/cloudscraper#dependencies.)'
                )
            raise
        except Exception:
            sys.tracebacklimit = 0
            raise RuntimeError('Error executing Cloudflare IUAM Javascript in nodejs')


# ------------------------------------------------------------------------------- #

ChallengeInterpreter()
