from __future__ import absolute_import
from ..exceptions import (
    reCaptchaParameter,
    reCaptchaTimeout,
    reCaptchaAPIError
)

try:
    from python_anticaptcha import (
        AnticaptchaClient,
        NoCaptchaTaskProxylessTask,
        HCaptchaTaskProxyless,
        AnticaptchaException
    )
except ImportError:
    raise ImportError(
        "Please install/upgrade the python module 'python_anticaptcha' via "
        "pip install python-anticaptcha or https://github.com/ad-m/python-anticaptcha/"
    )

import sys

from . import reCaptcha


class captchaSolver(reCaptcha):

    def __init__(self):
        if sys.modules['python_anticaptcha'].__version__ < '0.6':
            raise ImportError(
                "Please upgrade the python module 'python_anticaptcha' via "
                "pip install -U python-anticaptcha or https://github.com/ad-m/python-anticaptcha/"
            )
        super(captchaSolver, self).__init__('anticaptcha')

    # ------------------------------------------------------------------------------- #

    def getCaptchaAnswer(self, captchaType, url, siteKey, reCaptchaParams):
        if not reCaptchaParams.get('api_key'):
            raise reCaptchaParameter("anticaptcha: Missing api_key parameter.")

        client = AnticaptchaClient(reCaptchaParams.get('api_key'))

        if reCaptchaParams.get('proxy'):
            client.session.proxies = reCaptchaParams.get('proxies')

        captchaMap = {
            'reCaptcha': NoCaptchaTaskProxylessTask,
            'hCaptcha': HCaptchaTaskProxyless
        }

        task = captchaMap[captchaType](url, siteKey)

        if not hasattr(client, 'createTaskSmee'):
            raise NotImplementedError(
                "Please upgrade 'python_anticaptcha' via pip or download it from "
                "https://github.com/ad-m/python-anticaptcha/tree/hcaptcha"
            )

        job = client.createTaskSmee(task, timeout=180)

        try:
            job.join(maximum_time=180)
        except (AnticaptchaException) as e:
            raise reCaptchaTimeout('{}'.format(getattr(e, 'message', e)))

        if 'solution' in job._last_result:
            return job.get_solution_response()
        else:
            raise reCaptchaAPIError('Job did not return `solution` key in payload.')


# ------------------------------------------------------------------------------- #

captchaSolver()
