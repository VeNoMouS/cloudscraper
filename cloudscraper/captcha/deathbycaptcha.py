from __future__ import absolute_import

import json
import requests
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

try:
    import polling2
except ImportError:
    raise ImportError("Please install the python module 'polling2' via pip")

from ..exceptions import (
    CaptchaException,
    CaptchaServiceUnavailable,
    CaptchaTimeout,
    CaptchaParameter,
    CaptchaBadJobID,
    CaptchaReportError
)

from . import Captcha


class captchaSolver(Captcha):

    def __init__(self):
        super(captchaSolver, self).__init__('deathbycaptcha')
        self.host = 'http://api.dbcapi.me/api'
        self.session = requests.Session()
        self.captchaType = {
            'reCaptcha': '4',
            'hCaptcha': '7'
        }

    # ------------------------------------------------------------------------------- #

    @staticmethod
    def checkErrorStatus(response):
        errors = dict(
            [
                (400, "DeathByCaptcha: 400 Bad Request"),
                (403, "DeathByCaptcha: 403 Forbidden - Invalid credentails or insufficient credits."),
                # (500, "DeathByCaptcha: 500 Internal Server Error."),
                (503, "DeathByCaptcha: 503 Service Temporarily Unavailable.")
            ]
        )

        if response.status_code in errors:
            raise CaptchaServiceUnavailable(errors.get(response.status_code))

    # ------------------------------------------------------------------------------- #

    def login(self, username, password):
        self.username = username
        self.password = password

        def _checkRequest(response):
            if response.ok:
                if response.json().get('is_banned'):
                    raise CaptchaServiceUnavailable('DeathByCaptcha: Your account is banned.')

                if response.json().get('balanace') == 0:
                    raise CaptchaServiceUnavailable('DeathByCaptcha: insufficient credits.')

                return response

            self.checkErrorStatus(response)

            return None

        response = polling2.poll(
            lambda: self.session.post(
                f'{self.host}/user',
                headers={'Accept': 'application/json'},
                data={
                    'username': self.username,
                    'password': self.password
                }
            ),
            check_success=_checkRequest,
            step=10,
            timeout=120
        )

        self.debugRequest(response)

    # ------------------------------------------------------------------------------- #

    def reportJob(self, jobID):
        if not jobID:
            raise CaptchaBadJobID(
                "DeathByCaptcha: Error bad job id to report failed reCaptcha."
            )

        def _checkRequest(response):
            if response.status_code == 200:
                return response

            self.checkErrorStatus(response)

            return None

        response = polling2.poll(
            lambda: self.session.post(
                f'{self.host}/captcha/{jobID}/report',
                headers={'Accept': 'application/json'},
                data={
                    'username': self.username,
                    'password': self.password
                }
            ),
            check_success=_checkRequest,
            step=10,
            timeout=180
        )

        if response:
            return True
        else:
            raise CaptchaReportError(
                "DeathByCaptcha: Error report failed reCaptcha."
            )

    # ------------------------------------------------------------------------------- #

    def requestJob(self, jobID):
        if not jobID:
            raise CaptchaBadJobID(
                "DeathByCaptcha: Error bad job id to request reCaptcha."
            )

        def _checkRequest(response):
            if response.ok and response.json().get('text'):
                return response

            self.checkErrorStatus(response)

            return None

        response = polling2.poll(
            lambda: self.session.get(
                f'{self.host}/captcha/{jobID}',
                headers={'Accept': 'application/json'}
            ),
            check_success=_checkRequest,
            step=10,
            timeout=180
        )

        if response:
            return response.json().get('text')
        else:
            raise CaptchaTimeout(
                "DeathByCaptcha: Error failed to solve reCaptcha."
            )

    # ------------------------------------------------------------------------------- #

    def requestSolve(self, captchaType, url, siteKey):
        def _checkRequest(response):
            if response.ok and response.json().get("is_correct") and response.json().get('captcha'):
                return response

            self.checkErrorStatus(response)

            return None

        data = {
            'username': self.username,
            'password': self.password,
        }

        if captchaType == 'reCaptcha':
            jPayload = {
                'googlekey': siteKey,
                'pageurl': url
            }

            if self.proxy:
                jPayload.update({
                    'proxy': self.proxy,
                    'proxytype': self.proxyType
                })

            data.update({
                'type': self.captchaType[captchaType],
                'token_params': json.dumps(jPayload)
            })
        else:
            jPayload = {
                'sitekey': siteKey,
                'pageurl': url
            }

            if self.proxy:
                jPayload.update({
                    'proxy': self.proxy,
                    'proxytype': self.proxyType
                })

            data.update({
                'type': self.captchaType[captchaType],
                'hcaptcha_params': json.dumps(jPayload)
            })

        response = polling2.poll(
            lambda: self.session.post(
                f'{self.host}/captcha',
                headers={'Accept': 'application/json'},
                data=data,
                allow_redirects=False
            ),
            check_success=_checkRequest,
            step=10,
            timeout=180
        )

        if response:
            return response.json().get('captcha')
        else:
            raise CaptchaBadJobID(
                'DeathByCaptcha: Error no job id was returned.'
            )

    # ------------------------------------------------------------------------------- #

    def getCaptchaAnswer(self, captchaType, url, siteKey, captchaParams):
        jobID = None

        for param in ['username', 'password']:
            if not captchaParams.get(param):
                raise CaptchaParameter(
                    f"DeathByCaptcha: Missing '{param}' parameter."
                )
            setattr(self, param, captchaParams.get(param))

        if captchaParams.get('proxy') and not captchaParams.get('no_proxy'):
            hostParsed = urlparse(captchaParams.get('proxy', {}).get('https'))

            if not hostParsed.scheme:
                raise CaptchaParameter('Cannot parse proxy correctly, bad scheme')

            if not hostParsed.netloc:
                raise CaptchaParameter('Cannot parse proxy correctly, bad netloc')

            self.proxyType = hostParsed.scheme.upper()
            self.proxy = captchaParams.get('proxy', {}).get('https')
        else:
            self.proxy = None

        if captchaType not in self.captchaType:
            raise CaptchaException(f'DeathByCaptcha: {captchaType} is not supported by this provider.')

        try:
            jobID = self.requestSolve(captchaType, url, siteKey)
            return self.requestJob(jobID)
        except polling2.TimeoutException:
            try:
                if jobID:
                    self.reportJob(jobID)
            except polling2.TimeoutException:
                raise CaptchaTimeout(
                    f"DeathByCaptcha: Captcha solve took to long and also failed reporting the job id {jobID}."
                )

            raise CaptchaTimeout(
                f"DeathByCaptcha: Captcha solve took to long to execute job id {jobID}, aborting."
            )

# ------------------------------------------------------------------------------- #


captchaSolver()
