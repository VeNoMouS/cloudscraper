from __future__ import absolute_import

import requests

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

from ..exceptions import (
    CaptchaServiceUnavailable,
    CaptchaAPIError,
    CaptchaTimeout,
    CaptchaParameter,
    CaptchaBadJobID
)

try:
    import polling2
except ImportError:
    raise ImportError("Please install the python module 'polling2' via pip")

from . import Captcha


class captchaSolver(Captcha):

    def __init__(self):
        super(captchaSolver, self).__init__('anticaptcha')
        self.host = 'https://api.anti-captcha.com'
        self.session = requests.Session()
        self.captchaType = {
            'reCaptcha': 'NoCaptchaTask',
            'hCaptcha': 'HCaptchaTask',
            'turnstile': 'TurnstileTask'
        }

    # ------------------------------------------------------------------------------- #

    @staticmethod
    def checkErrorStatus(response):
        if response.status_code in [500, 502]:
            raise CaptchaServiceUnavailable(
                f'anticaptcha: Server Side Error {response.status_code}'
            )

        payload = response.json()
        if payload['errorId'] >= 1:
            if 'errorDescription' in payload:
                raise CaptchaAPIError(
                    payload['errorDescription']
                )
            else:
                raise CaptchaAPIError(payload['errorCode'])

    # ------------------------------------------------------------------------------- #

    def requestJob(self, taskID):
        if not taskID:
            raise CaptchaBadJobID(
                'anticaptcha: Error bad task id to request Captcha.'
            )

        def _checkRequest(response):
            self.checkErrorStatus(response)

            if response.ok and response.json()['status'] == 'ready':
                return True

            return None

        response = polling2.poll(
            lambda: self.session.post(
                f'{self.host}/getTaskResult',
                json={
                    'clientKey': self.clientKey,
                    'taskId': taskID
                },
                timeout=30
            ),
            check_success=_checkRequest,
            step=5,
            timeout=180
        )

        if response:
            payload = response.json()['solution']
            if 'token' in payload:
                return payload['token']
            else:
                return payload['gRecaptchaResponse']
        else:
            raise CaptchaTimeout(
                "anticaptcha: Error failed to solve Captcha."
            )

    # ------------------------------------------------------------------------------- #

    def requestSolve(self, captchaType, url, siteKey):
        def _checkRequest(response):
            self.checkErrorStatus(response)

            if response.ok and response.json()['taskId']:
                return True

            return None

        data = {
            'clientKey': self.clientKey,
            'task': {
                'websiteURL': url,
                'websiteKey': siteKey,
                'type': self.captchaType[captchaType]
            },
            'softId': 959
        }

        if self.proxy:
            data['task'].update(self.proxy)
        else:
            data['task']['type'] = f"{data['task']['type']}Proxyless"

        response = polling2.poll(
            lambda: self.session.post(
                f'{self.host}/createTask',
                json=data,
                allow_redirects=False,
                timeout=30
            ),
            check_success=_checkRequest,
            step=5,
            timeout=180
        )

        if response:
            return response.json()['taskId']
        else:
            raise CaptchaBadJobID(
                'anticaptcha: Error no task id was returned.'
            )

    # ------------------------------------------------------------------------------- #

    def getCaptchaAnswer(self, captchaType, url, siteKey, captchaParams):
        taskID = None

        if not captchaParams.get('clientKey'):
            raise CaptchaParameter(
                "anticaptcha: Missing clientKey parameter."
            )

        self.clientKey = captchaParams.get('clientKey')

        if captchaParams.get('proxy') and not captchaParams.get('no_proxy'):
            hostParsed = urlparse(captchaParams.get('proxy', {}).get('https'))

            if not hostParsed.scheme:
                raise CaptchaParameter('Cannot parse proxy correctly, bad scheme')

            if not hostParsed.netloc:
                raise CaptchaParameter('Cannot parse proxy correctly, bad netloc')

            ports = {
                'http': 80,
                'https': 443
            }

            self.proxy = {
                'proxyType': hostParsed.scheme,
                'proxyAddress': hostParsed.hostname,
                'proxyPort': hostParsed.port if hostParsed.port else ports[self.proxy['proxyType']],
                'proxyLogin': hostParsed.username,
                'proxyPassword': hostParsed.password,
            }
        else:
            self.proxy = None

        try:
            taskID = self.requestSolve(captchaType, url, siteKey)
            return self.requestJob(taskID)
        except polling2.TimeoutException:
            try:
                if taskID:
                    self.reportJob(taskID)
            except polling2.TimeoutException:
                raise CaptchaTimeout(
                    "anticaptcha: Captcha solve took to long and also failed "
                    f"reporting the task with task id {taskID}."
                )

            raise CaptchaTimeout(
                "anticaptcha: Captcha solve took to long to execute "
                f"task id {taskID}, aborting."
            )


# ------------------------------------------------------------------------------- #

captchaSolver()
