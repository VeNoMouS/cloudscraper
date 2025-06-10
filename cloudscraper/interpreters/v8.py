from __future__ import absolute_import

import sys

try:
    import v8eval
except ImportError:
    sys.tracebacklimit = 0
    raise RuntimeError('Please install the python module v8eval either via pip or download it from https://github.com/sony/v8eval')

from . import JavaScriptInterpreter
from .encapsulated import template

# ------------------------------------------------------------------------------- #


class ChallengeInterpreter(JavaScriptInterpreter):

    def __init__(self):
        super(ChallengeInterpreter, self).__init__('v8')

    # ------------------------------------------------------------------------------- #

    def eval(self, body, domain):
        try:
            return v8eval.V8().eval(template(body, domain))
        except (TypeError, v8eval.V8Error):
            RuntimeError('We encountered an error running the V8 Engine.')


# ------------------------------------------------------------------------------- #

ChallengeInterpreter()
