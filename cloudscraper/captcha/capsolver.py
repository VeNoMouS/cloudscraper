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
        super(captchaSolver, self).__init__('capsolver')
        self.host = 'https://api.capsolver.com'
        self.session = requests.Session()
        self.captchaType = {
            'reCaptcha': 'ReCaptchaV2Task',
            'hCaptcha': 'HCaptchaTask',
            'turnstile': 'AntiCloudflareTask'
        }

    # ------------------------------------------------------------------------------- #

    @staticmethod
    def checkErrorStatus(response, fnct):
        if response.status_code in [500, 502]:
            raise CaptchaServiceUnavailable(f'CapSolver: Server Side Error {response.status_code}')

        try:
            rPayload = response.json()
        except Exception:
            return

        if rPayload.get('errorDescription', False) and 'Current system busy' not in rPayload['errorDescription']:
            raise CaptchaAPIError(
                f"CapSolver -> {fnct} -> {rPayload.get('errorDescription')}"
            )

    # ------------------------------------------------------------------------------- #

    def requestJob(self, jobID):
        if not jobID:
            raise CaptchaBadJobID("CapSolver: Error bad job id to request task result.")

        def _checkRequest(response):
            self.checkErrorStatus(response, 'requestJob')
            try:
                if response.ok and response.json()['status'] == 'ready':
                    return True
            except Exception:
                pass
            return None

        response = polling2.poll(
            lambda: self.session.post(
                f'{self.host}/getTaskResult',
                json={
                    'clientKey': self.api_key,
                    'taskId': jobID
                },
                timeout=30
            ),
            check_success=_checkRequest,
            step=5,
            timeout=180
        )

        if response:
            try:
                rPayload = response.json()['solution']
                if 'token' in rPayload:
                    return rPayload['token']
                else:
                    return rPayload['gRecaptchaResponse']
            except Exception:
                pass

        raise CaptchaTimeout(
            "CapSolver: Error failed to solve Captcha."
        )

    # ------------------------------------------------------------------------------- #

    def requestSolve(self, captchaType, url, siteKey):

        # ------------------------------------------------------------------------------- #

        def _checkRequest(response):
            self.checkErrorStatus(response, 'createTask')
            try:
                rPayload = response.json()
                if response.ok:
                    if rPayload.get("taskId", False):
                        return True
            except Exception:
                pass
            return None

        # ------------------------------------------------------------------------------- #

        payload = {
            'clientKey': self.api_key,
            'appId': '9E717405-8C70-49B3-B277-7C2F2196484B',
            'task': {
                'type': self.captchaType[captchaType],
                'websiteURL': url,
                'websiteKey': siteKey
            }
        }

        if captchaType == 'turnstile':
            payload['task']['metadata'] = {'type': 'turnstile'}

        if self.proxy:
            payload['task']['proxy'] = self.proxy
        else:
            payload['task']['type'] = f"{self.captchaType[captchaType]}Proxyless"

        response = polling2.poll(
            lambda: self.session.post(
                f'{self.host}/createTask',
                json=payload,
                allow_redirects=False,
                timeout=30
            ),
            check_success=_checkRequest,
            step=5,
            timeout=180
        )

        if response:
            rPayload = response.json()
            if rPayload.get('taskId'):
                return rPayload['taskId']

        raise CaptchaBadJobID(
            'CapSolver: Error no job id was returned.'
        )

    # ------------------------------------------------------------------------------- #

    def getCaptchaAnswer(self, captchaType, url, siteKey, captchaParams):
        if not captchaParams.get('api_key'):
            raise CaptchaParameter("CapSolver: Missing api_key parameter.")
        self.api_key = captchaParams.get('api_key')

        if captchaParams.get('proxy') and not captchaParams.get('no_proxy'):
            hostParsed = urlparse(captchaParams.get('proxy', {}).get('https'))

            if not hostParsed.scheme:
                raise CaptchaParameter('Cannot parse proxy correctly, bad scheme')

            if not hostParsed.netloc:
                raise CaptchaParameter('Cannot parse proxy correctly, bad netloc')

            self.proxy = captchaParams['proxy']['https']
        else:
            self.proxy = None

        try:
            jobID = self.requestSolve(captchaType, url, siteKey)
            return self.requestJob(jobID)
        except polling2.TimeoutException:
            raise CaptchaTimeout(
                f"CapSolver: Captcha solve (task ID: {jobID}) took to long."
            )

        raise CaptchaAPIError('CapSolver: Job Failure.')


# ------------------------------------------------------------------------------- #

captchaSolver()
