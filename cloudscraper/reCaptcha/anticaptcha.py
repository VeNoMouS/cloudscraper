from __future__ import absolute_import

import sys
import reCaptcha_exceptions

try:
    from python_anticaptcha import AnticaptchaClient, NoCaptchaTaskProxylessTask
except ImportError:
    sys.tracebacklimit = 0
    raise reCaptcha_exceptions.reCaptcha_Import_Error(
        "Please install the python module 'python_anticaptcha' via pip or download it from "
        "https://github.com/ad-m/python-anticaptcha"
    )

from . import reCaptcha


class captchaSolver(reCaptcha):

    def __init__(self):
        super(captchaSolver, self).__init__('anticaptcha')

    # ------------------------------------------------------------------------------- #

    def getCaptchaAnswer(self, site_url, site_key, reCaptchaParams):
        if not reCaptchaParams.get('api_key'):
            raise reCaptcha_exceptions.reCaptcha_Bad_Parameter("anticaptcha: Missing api_key parameter.")

        client = AnticaptchaClient(reCaptchaParams.get('api_key'))

        if reCaptchaParams.get('proxy'):
            client.session.proxies = reCaptchaParams.get('proxies')

        task = NoCaptchaTaskProxylessTask(site_url, site_key)

        if not hasattr(client, 'createTaskSmee'):
            sys.tracebacklimit = 0
            raise reCaptcha_exceptions.reCaptcha_Import_Error(
                "Please upgrade 'python_anticaptcha' via pip or download it from https://github.com/ad-m/python-anticaptcha"
            )

        job = client.createTaskSmee(task)
        return job.get_solution_response()


# ------------------------------------------------------------------------------- #

captchaSolver()
