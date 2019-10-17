from __future__ import absolute_import

import requests

try:
    import polling
except ImportError:
    import sys
    sys.tracebacklimit = 0
    raise RuntimeError("Please install the python module 'polling' via pip or download it from https://github.com/justiniso/polling/")

from . import reCaptcha


class captchaSolver(reCaptcha):

    def __init__(self):
        super(captchaSolver, self).__init__('2captcha')
        self.host = 'https://2captcha.com'
        self.session = requests.Session()

    # ------------------------------------------------------------------------------- #

    @staticmethod
    def checkErrorStatus(response, request_type):
        if response.status_code in [500, 502]:
            raise RuntimeError('2Captcha: Server Side Error {}'.format(response.status_code))

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

        if response.json().get('status') is False and response.json().get('request') in errors.get(request_type):
            raise RuntimeError('{} {}'.format(response.json().get('request'), errors.get(request_type).get(response.json().get('request'))))

    # ------------------------------------------------------------------------------- #

    def reportJob(self, jobID):
        if not jobID:
            raise RuntimeError("2Captcha: Error bad job id to request reCaptcha.")

        def _checkRequest(response):
            if response.status_code in [200, 303] and response.json().get('status') == 1:
                return response

            self.checkErrorStatus(response, 'res.php')

            return None

        response = polling.poll(
            lambda: self.session.get(
                '{}/res.php'.format(self.host),
                params={
                    'key': self.api_key,
                    'action': 'reportbad',
                    'id': jobID,
                    'json': '1'
                }
            ),
            check_success=_checkRequest,
            step=5,
            timeout=180
        )

        if response:
            return True
        else:
            raise RuntimeError("2Captcha: Error - Failed to report bad reCaptcha solve.")

    # ------------------------------------------------------------------------------- #

    def requestJob(self, jobID):
        if not jobID:
            raise RuntimeError("2Captcha: Error bad job id to request reCaptcha.")

        def _checkRequest(response):
            if response.status_code in [200, 303] and response.json().get('status') == 1:
                return response

            self.checkErrorStatus(response, 'res.php')

            return None

        response = polling.poll(
            lambda: self.session.get(
                '{}/res.php'.format(self.host),
                params={
                    'key': self.api_key,
                    'action': 'get',
                    'id': jobID,
                    'json': '1'
                }
            ),
            check_success=_checkRequest,
            step=5,
            timeout=180
        )

        if response:
            return response.json().get('request')
        else:
            raise RuntimeError("2Captcha: Error failed to solve reCaptcha.")

    # ------------------------------------------------------------------------------- #

    def requestSolve(self, site_url, site_key):
        def _checkRequest(response):
            if response.status_code in [200, 303] and response.json().get("status") == 1 and response.json().get('request'):
                return response

            self.checkErrorStatus(response, 'in.php')

            return None

        response = polling.poll(
            lambda: self.session.post(
                '{}/in.php'.format(self.host),
                data={
                    'key': self.api_key,
                    'method': 'userrecaptcha',
                    'googlekey': site_key,
                    'pageurl': site_url,
                    'json': '1',
                    'soft_id': '5507698'
                },
                allow_redirects=False
            ),
            check_success=_checkRequest,
            step=5,
            timeout=180
        )

        if response:
            return response.json().get('request')
        else:
            raise RuntimeError('2Captcha: Error no job id was returned.')

    # ------------------------------------------------------------------------------- #

    def getCaptchaAnswer(self, site_url, site_key, reCaptchaParams):
        jobID = None

        if not reCaptchaParams.get('api_key'):
            raise ValueError("2Captcha: Missing api_key parameter.")

        self.api_key = reCaptchaParams.get('api_key')

        if reCaptchaParams.get('proxy'):
            self.session.proxies = reCaptchaParams.get('proxies')

        try:
            jobID = self.requestSolve(site_url, site_key)
            return self.requestJob(jobID)
        except polling.TimeoutException:
            try:
                if jobID:
                    self.reportJob(jobID)
            except polling.TimeoutException:
                raise RuntimeError("2Captcha: reCaptcha solve took to long and also failed reporting the job.")

            raise RuntimeError("2Captcha: reCaptcha solve took to long to execute, aborting.")


# ------------------------------------------------------------------------------- #

captchaSolver()
