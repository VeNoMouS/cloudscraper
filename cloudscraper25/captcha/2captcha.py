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
    CaptchaBadJobID,
    CaptchaReportError
)

try:
    import polling2
except ImportError:
    raise ImportError("Please install the python module 'polling2' via pip")

from . import Captcha


class captchaSolver(Captcha):

    def __init__(self):
        super(captchaSolver, self).__init__('2captcha')
        self.host = 'https://2captcha.com'
        self.session = requests.Session()
        self.captchaType = {
            'reCaptcha': 'userrecaptcha',
            'hCaptcha': 'hcaptcha',
            'turnstile': 'turnstile'
        }

    # ------------------------------------------------------------------------------- #

    @staticmethod
    def checkErrorStatus(response, request_type):
        if response.status_code in [500, 502]:
            raise CaptchaServiceUnavailable(f'2Captcha: Server Side Error {response.status_code}')

        errors = {
            'in.php': {
                "ERROR_WRONG_USER_KEY": "You've provided api_key parameter value is in incorrect format, it should contain 32 symbols.",
                "ERROR_KEY_DOES_NOT_EXIST": "The api_key you've provided does not exists.",
                "ERROR_ZERO_BALANCE": "You don't have sufficient funds on your account.",
                "ERROR_PAGEURL": "pageurl parameter is missing in your request.",
                "ERROR_NO_SLOT_AVAILABLE":
                    "No Slots Available.\nYou can receive this error in two cases:\n"
                    "1. If you solve ReCaptcha: the queue of your captchas that are not distributed to workers is too long. "
                    "Queue limit changes dynamically and depends on total amount of captchas awaiting solution and usually it's between 50 and 100 captchas.\n"
                    "2. If you solve Normal Captcha: your maximum rate for normal captchas is lower than current rate on the server."
                    "You can change your maximum rate in your account's settings.",
                "ERROR_IP_NOT_ALLOWED": "The request is sent from the IP that is not on the list of your allowed IPs.",
                "IP_BANNED": "Your IP address is banned due to many frequent attempts to access the server using wrong authorization keys.",
                "ERROR_BAD_TOKEN_OR_PAGEURL":
                    "You can get this error code when sending ReCaptcha V2. "
                    "That happens if your request contains invalid pair of googlekey and pageurl. "
                    "The common reason for that is that ReCaptcha is loaded inside an iframe hosted on another domain/subdomain.",
                "ERROR_GOOGLEKEY":
                    "You can get this error code when sending ReCaptcha V2. "
                    "That means that sitekey value provided in your request is incorrect: it's blank or malformed.",
                "MAX_USER_TURN": "You made more than 60 requests within 3 seconds.Your account is banned for 10 seconds. Ban will be lifted automatically."
            },
            'res.php': {
                "ERROR_CAPTCHA_UNSOLVABLE":
                    "We are unable to solve your captcha - three of our workers were unable solve it "
                    "or we didn't get an answer within 90 seconds (300 seconds for ReCaptcha V2). "
                    "We will not charge you for that request.",
                "ERROR_WRONG_USER_KEY": "You've provided api_key parameter value in incorrect format, it should contain 32 symbols.",
                "ERROR_KEY_DOES_NOT_EXIST": "The api_key you've provided does not exists.",
                "ERROR_WRONG_ID_FORMAT": "You've provided captcha ID in wrong format. The ID can contain numbers only.",
                "ERROR_WRONG_CAPTCHA_ID": "You've provided incorrect captcha ID.",
                "ERROR_BAD_DUPLICATES":
                    "Error is returned when 100% accuracy feature is enabled. "
                    "The error means that max numbers of tries is reached but min number of matches not found.",
                "REPORT_NOT_RECORDED": "Error is returned to your complain request if you already complained lots of correctly solved captchas.",
                "ERROR_IP_ADDRES":
                    "You can receive this error code when registering a pingback (callback) IP or domain."
                    "That happes if your request is coming from an IP address that doesn't match the IP address of your pingback IP or domain.",
                "ERROR_TOKEN_EXPIRED": "You can receive this error code when sending GeeTest. That error means that challenge value you provided is expired.",
                "ERROR_EMPTY_ACTION": "Action parameter is missing or no value is provided for action parameter."
            }
        }

        rPayload = response.json()
        if rPayload.get('status') == 0 and rPayload.get('request') in errors.get(request_type):
            raise CaptchaAPIError(
                f"{rPayload['request']} {errors.get(request_type).get(rPayload['request'])}"
            )

    # ------------------------------------------------------------------------------- #

    def reportJob(self, jobID):
        if not jobID:
            raise CaptchaBadJobID(
                "2Captcha: Error bad job id to request Captcha."
            )

        def _checkRequest(response):
            self.checkErrorStatus(response, 'res.php')
            if response.ok and response.json().get('status') == 1:
                return response
            return None

        response = polling2.poll(
            lambda: self.session.get(
                f'{self.host}/res.php',
                params={
                    'key': self.api_key,
                    'action': 'reportbad',
                    'id': jobID,
                    'json': '1'
                },
                timeout=30
            ),
            check_success=_checkRequest,
            step=5,
            timeout=180
        )

        if response:
            return True
        else:
            raise CaptchaReportError(
                "2Captcha: Error - Failed to report bad Captcha solve."
            )

    # ------------------------------------------------------------------------------- #

    def requestJob(self, jobID):
        if not jobID:
            raise CaptchaBadJobID("2Captcha: Error bad job id to request Captcha.")

        def _checkRequest(response):
            self.checkErrorStatus(response, 'res.php')
            if response.ok and response.json().get('status') == 1:
                return response
            return None

        response = polling2.poll(
            lambda: self.session.get(
                f'{self.host}/res.php',
                params={
                    'key': self.api_key,
                    'action': 'get',
                    'id': jobID,
                    'json': '1'
                },
                timeout=30
            ),
            check_success=_checkRequest,
            step=5,
            timeout=180
        )

        if response:
            return response.json().get('request')
        else:
            raise CaptchaTimeout(
                "2Captcha: Error failed to solve Captcha."
            )

    # ------------------------------------------------------------------------------- #

    def requestSolve(self, captchaType, url, siteKey):
        def _checkRequest(response):
            self.checkErrorStatus(response, 'in.php')
            if response.ok and response.json().get("status") == 1 and response.json().get('request'):
                return response
            return None

        data = {
            'key': self.api_key,
            'pageurl': url,
            'json': 1,
            'soft_id': 2905
        }

        data.update({
            'method': self.captchaType[captchaType],
            'googlekey' if captchaType == 'reCaptcha' else 'sitekey': siteKey
        })

        if self.proxy:
            data.update({
                'proxy': self.proxy,
                'proxytype': self.proxyType
            })

        response = polling2.poll(
            lambda: self.session.post(
                f'{self.host}/in.php',
                data=data,
                allow_redirects=False,
                timeout=30
            ),
            check_success=_checkRequest,
            step=5,
            timeout=180
        )

        if response:
            return response.json().get('request')
        else:
            raise CaptchaBadJobID(
                '2Captcha: Error no job id was returned.'
            )

    # ------------------------------------------------------------------------------- #

    def getCaptchaAnswer(self, captchaType, url, siteKey, captchaParams):
        jobID = None

        if not captchaParams.get('api_key'):
            raise CaptchaParameter(
                "2Captcha: Missing api_key parameter."
            )

        self.api_key = captchaParams.get('api_key')

        if captchaParams.get('proxy') and not captchaParams.get('no_proxy'):
            hostParsed = urlparse(captchaParams.get('proxy', {}).get('https'))

            if not hostParsed.scheme:
                raise CaptchaParameter('Cannot parse proxy correctly, bad scheme')

            if not hostParsed.netloc:
                raise CaptchaParameter('Cannot parse proxy correctly, bad netloc')

            self.proxyType = hostParsed.scheme
            self.proxy = hostParsed.netloc
        else:
            self.proxy = None

        try:
            jobID = self.requestSolve(captchaType, url, siteKey)
            return self.requestJob(jobID)
        except polling2.TimeoutException:
            try:
                if jobID:
                    self.reportJob(jobID)
            except polling2.TimeoutException:
                raise CaptchaTimeout(
                    f"2Captcha: Captcha solve took to long and also failed reporting the job the job id {jobID}."
                )

            raise CaptchaTimeout(
                f"2Captcha: Captcha solve took to long to execute job id {jobID}, aborting."
            )


# ------------------------------------------------------------------------------- #

captchaSolver()
