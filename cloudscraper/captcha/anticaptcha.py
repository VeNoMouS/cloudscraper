from __future__ import absolute_import
from ..exceptions import (
    CaptchaParameter,
    CaptchaTimeout,
    CaptchaAPIError
)

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

try:
    from python_anticaptcha import (
        AnticaptchaClient,
        NoCaptchaTaskProxylessTask,
        HCaptchaTaskProxyless,
        NoCaptchaTask,
        HCaptchaTask,
        AnticaptchaException
    )
except ImportError:
    raise ImportError(
        "Please install/upgrade the python module 'python_anticaptcha' via "
        "pip install python-anticaptcha or https://github.com/ad-m/python-anticaptcha/"
    )

import sys

from . import Captcha


class captchaSolver(Captcha):

    def __init__(self):
        if sys.modules['python_anticaptcha'].__version__ < '0.6':
            raise ImportError(
                "Please upgrade the python module 'python_anticaptcha' via "
                "pip install -U python-anticaptcha or https://github.com/ad-m/python-anticaptcha/"
            )
        super(captchaSolver, self).__init__('anticaptcha')

    # ------------------------------------------------------------------------------- #

    def parseProxy(self, url, user_agent):
        parsed = urlparse(url)

        return dict(
            proxy_type=parsed.scheme,
            proxy_address=parsed.hostname,
            proxy_port=parsed.port,
            proxy_login=parsed.username,
            proxy_password=parsed.password,
            user_agent=user_agent
        )

    # ------------------------------------------------------------------------------- #

    def getCaptchaAnswer(self, captchaType, url, siteKey, captchaParams):
        if not captchaParams.get('api_key'):
            raise CaptchaParameter("anticaptcha: Missing api_key parameter.")

        client = AnticaptchaClient(captchaParams.get('api_key'))

        if captchaParams.get('proxy') and not captchaParams.get('no_proxy'):
            captchaMap = {
                'reCaptcha': NoCaptchaTask,
                'hCaptcha': HCaptchaTask
            }

            proxy = self.parseProxy(
                captchaParams.get('proxy', {}).get('https'),
                captchaParams.get('User-Agent', '')
            )

            task = captchaMap[captchaType](
                url,
                siteKey,
                **proxy
            )
        else:
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
            raise CaptchaTimeout('{}'.format(getattr(e, 'message', e)))

        if 'solution' in job._last_result:
            return job.get_solution_response()
        else:
            raise CaptchaAPIError('Job did not return `solution` key in payload.')


# ------------------------------------------------------------------------------- #

captchaSolver()
