from __future__ import absolute_import

from ..exceptions import reCaptchaParameter

try:
    from python_anticaptcha import (
        AnticaptchaClient,
        NoCaptchaTaskProxylessTask,
        HCaptchaTaskProxyless
    )
except ImportError:
    raise ImportError(
        "Please install/upgrade the python module 'python_anticaptcha' via "
        "pip install git+https://github.com/ad-m/python-anticaptcha.git@hcaptcha or "
        "https://github.com/ad-m/python-anticaptcha/tree/hcaptcha"
    )

from . import reCaptcha


class captchaSolver(reCaptcha):

    def __init__(self):
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

        job = client.createTaskSmee(task)
        return job.get_solution_response()


# ------------------------------------------------------------------------------- #

captchaSolver()
