from __future__ import absolute_import

import sys

try:
    from python_anticaptcha import AnticaptchaClient, NoCaptchaTaskProxylessTask, NoCaptchaTask, Proxy
except ImportError:
    sys.tracebacklimit = 0
    raise RuntimeError("Please install the python module 'python_anticaptcha' via pip or download it https://github.com/ad-m/python-anticaptcha")

from . import reCaptcha


class captchaSolver(reCaptcha):

    def __init__(self):
        super(captchaSolver, self).__init__('anticaptcha')

    def getCaptchaAnswer(self, site_url, site_key, reCaptchaParams):
        if not reCaptchaParams.get('api_key'):
            raise ValueError("reCaptcha provider 'anticaptcha' was not provided an 'api_key' parameter.")

        client = AnticaptchaClient(reCaptchaParams.get('api_key'))

        if reCaptchaParams.get('proxy', False) and reCaptchaParams.get('proxies'):
            client.session.proxies = reCaptchaParams.get('proxies')
            task = NoCaptchaTask(
                site_url,
                site_key,
                proxy=Proxy.parse_url(
                    reCaptchaParams.get('proxies').get('https')
                )
            )
        else:
            task = NoCaptchaTaskProxylessTask(site_url, site_key)

        job = client.createTask(task)
        job.join()
        return job.get_solution_response()


captchaSolver()
