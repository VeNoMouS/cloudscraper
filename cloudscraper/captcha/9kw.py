from __future__ import absolute_import

import re
import requests

try:
    import polling
except ImportError:
    raise ImportError(
        "Please install the python module 'polling' via pip or download it from "
        "https://github.com/justiniso/polling/"
    )

from ..exceptions import (
    CaptchaException,
    CaptchaServiceUnavailable,
    CaptchaAPIError,
    CaptchaTimeout,
    CaptchaParameter,
    CaptchaBadJobID
)

from . import Captcha


class captchaSolver(Captcha):

    def __init__(self):
        super(captchaSolver, self).__init__('9kw')
        self.host = 'https://www.9kw.eu/index.cgi'
        self.maxtimeout = 180
        self.session = requests.Session()
        self.captchaType = {
            'reCaptcha': 'recaptchav2',
            'hCaptcha': 'hcaptcha'
        }

    # ------------------------------------------------------------------------------- #

    @staticmethod
    def checkErrorStatus(response):
        if response.status_code in [500, 502]:
            raise CaptchaServiceUnavailable(
                f'9kw: Server Side Error {response.status_code}'
            )

        error_codes = {
            1: 'No API Key available.',
            2: 'No API key found.',
            3: 'No active API key found.',
            4: 'API Key has been disabled by the operator. ',
            5: 'No user found.',
            6: 'No data found.',
            7: 'Found No ID.',
            8: 'found No captcha.',
            9: 'No image found.',
            10: 'Image size not allowed.',
            11: 'credit is not sufficient.',
            12: 'what was done.',
            13: 'No answer contain.',
            14: 'Captcha already been answered.',
            15: 'Captcha to quickly filed.',
            16: 'JD check active.',
            17: 'Unknown problem.',
            18: 'Found No ID.',
            19: 'Incorrect answer.',
            20: 'Do not timely filed (Incorrect UserID).',
            21: 'Link not allowed.',
            22: 'Prohibited submit.',
            23: 'Entering prohibited.',
            24: 'Too little credit.',
            25: 'No entry found.',
            26: 'No Conditions accepted.',
            27: 'No coupon code found in the database.',
            28: 'Already unused voucher code.',
            29: 'maxTimeout under 60 seconds.',
            30: 'User not found.',
            31: 'An account is not yet 24 hours in system.',
            32: 'An account does not have the full rights.',
            33: 'Plugin needed a update.',
            34: 'No HTTPS allowed.',
            35: 'No HTTP allowed.',
            36: 'Source not allowed.',
            37: 'Transfer denied.',
            38: 'Incorrect answer without space',
            39: 'Incorrect answer with space',
            40: 'Incorrect answer with not only numbers',
            41: 'Incorrect answer with not only A-Z, a-z',
            42: 'Incorrect answer with not only 0-9, A-Z, a-z',
            43: 'Incorrect answer with not only [0-9,- ]',
            44: 'Incorrect answer with not only [0-9A-Za-z,- ]',
            45: 'Incorrect answer with not only coordinates',
            46: 'Incorrect answer with not only multiple coordinates',
            47: 'Incorrect answer with not only data',
            48: 'Incorrect answer with not only rotate number',
            49: 'Incorrect answer with not only text',
            50: 'Incorrect answer with not only text and too short',
            51: 'Incorrect answer with not enough chars',
            52: 'Incorrect answer with too many chars',
            53: 'Incorrect answer without no or yes',
            54: 'Assignment was not found.'
        }

        if response.text.startswith('{'):
            if response.json().get('error'):
                raise CaptchaAPIError(error_codes.get(int(response.json().get('error'))))
        else:
            error_code = int(re.search(r'^00(?P<error_code>\d+)', response.text).groupdict().get('error_code', 0))
            if error_code:
                raise CaptchaAPIError(error_codes.get(error_code))

    # ------------------------------------------------------------------------------- #

    def requestJob(self, jobID):
        if not jobID:
            raise CaptchaBadJobID(
                "9kw: Error bad job id to request against."
            )

        def _checkRequest(response):
            if response.ok and response.json().get('answer') != 'NO DATA':
                return response

            self.checkErrorStatus(response)

            return None

        response = polling.poll(
            lambda: self.session.get(
                self.host,
                params={
                    'apikey': self.api_key,
                    'action': 'usercaptchacorrectdata',
                    'id': jobID,
                    'info': 1,
                    'json': 1
                }
            ),
            check_success=_checkRequest,
            step=10,
            timeout=(self.maxtimeout + 10)
        )

        if response:
            return response.json().get('answer')
        else:
            raise CaptchaTimeout("9kw: Error failed to solve.")

    # ------------------------------------------------------------------------------- #

    def requestSolve(self, captchaType, url, siteKey):
        def _checkRequest(response):
            if response.ok and response.text.startswith('{') and response.json().get('captchaid'):
                return response

            self.checkErrorStatus(response)

            return None

        response = polling.poll(
            lambda: self.session.post(
                self.host,
                data={
                    'apikey': self.api_key,
                    'action': 'usercaptchaupload',
                    'interactive': 1,
                    'file-upload-01': siteKey,
                    'oldsource': self.captchaType[captchaType],
                    'pageurl': url,
                    'maxtimeout': self.maxtimeout,
                    'json': 1
                },
                allow_redirects=False
            ),
            check_success=_checkRequest,
            step=5,
            timeout=(self.maxtimeout + 10)
        )

        if response:
            return response.json().get('captchaid')
        else:
            raise CaptchaBadJobID('9kw: Error no valid job id was returned.')

    # ------------------------------------------------------------------------------- #
    def getCaptchaAnswer(self, captchaType, url, siteKey, captchaParams):
        jobID = None

        if not captchaParams.get('api_key'):
            raise CaptchaParameter("9kw: Missing api_key parameter.")

        self.api_key = captchaParams.get('api_key')

        if captchaParams.get('maxtimeout'):
            self.maxtimeout = captchaParams.get('maxtimeout')

        if captchaParams.get('proxy'):
            self.session.proxies = captchaParams.get('proxies')

        if captchaType not in self.captchaType:
            raise CaptchaException(f'9kw: {captchaType} is not supported by this provider.')

        try:
            jobID = self.requestSolve(captchaType, url, siteKey)
            return self.requestJob(jobID)
        except polling.TimeoutException:
            raise CaptchaTimeout(
                f"9kw: solve took to long to execute 'captchaid' {jobID}, aborting."
            )


# ------------------------------------------------------------------------------- #

captchaSolver()
