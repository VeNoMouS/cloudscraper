from __future__ import absolute_import

import requests

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
        self.host = 'https://api.capsolver.com'
        self.session = requests.Session()
        super(captchaSolver, self).__init__('CapSolver')

    # ------------------------------------------------------------------------------- #

    @staticmethod
    def checkErrorStatus(response, request_type):
        if response.status_code in [500, 502]:
            raise CaptchaServiceUnavailable(f'CapSolver: Server Side Error {response.status_code}')

        try:
            rPayload = response.json()
        except Exception:
            return

        if rPayload.get('errorDescription', False) and 'Current system busy' not in rayload['errorDescription']:
            raise CaptchaAPIError(
                f"CapSolver: {request_type} -> {rPayload.get('errorDescription')}"
            )

    # ------------------------------------------------------------------------------- #

    def requestJob(self, jobID):
        if not jobID:
            raise CaptchaBadJobID("CapSolver: Error bad job id to request task result.")

        def _checkRequest(response):
            self.checkErrorStatus(response, 'getTaskResult')
            try:
                rPayload = response.json()
                if response.ok:
                    if rPayload.get("solution", {}).get('gRecaptchaResponse'):
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
                rPayload = response.json()
                if rPayload.get('solution', {}).get('gRecaptchaResponse'):
                    return rPayload['solution']['gRecaptchaResponse']
            except Exception:
                pass

        raise CaptchaTimeout(
            "CapSolver: Error failed to solve Captcha."
        )

    # ------------------------------------------------------------------------------- #

    def requestSolve(self, captchaType, url, siteKey):
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

        response = polling2.poll(
            lambda: self.session.post(
                f'{self.host}/createTask',
                json={
                    'clientKey': self.api_key,
                    'appId': '9E717405-8C70-49B3-B277-7C2F2196484B',
                    'task': {
                        'type': 'HCaptchaTaskProxyless',
                        'websiteURL': url,
                        'websiteKey': siteKey
                    }
                },
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
