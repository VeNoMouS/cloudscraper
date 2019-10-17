from __future__ import absolute_import

import json
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
        super(captchaSolver, self).__init__('deathbycaptcha')
        self.host = 'http://api.dbcapi.me/api'
        self.session = requests.Session()

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
            raise RuntimeError(errors.get(response.status_code))

        # ------------------------------------------------------------------------------- #

    def login(self, username, password):
        self.username = username
        self.password = password

        def _checkRequest(response):
            if response.status_code == 200:
                if response.json().get('is_banned'):
                    raise RuntimeError('DeathByCaptcha: Your account is banned.')

                if response.json().get('balanace') == 0:
                    raise RuntimeError('DeathByCaptcha: insufficient credits.')

                return response

            self.checkErrorStatus(response)

            return None

        response = polling.poll(
            lambda: self.session.post(
                '{}/user'.format(self.host),
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
            raise RuntimeError("DeathByCaptcha: Error bad job id to report failed reCaptcha.")

        def _checkRequest(response):
            if response.status_code == 200:
                return response

            self.checkErrorStatus(response)

            return None

        response = polling.poll(
            lambda: self.session.post(
                '{}/captcha/{}/report'.format(self.host, jobID),
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
            raise RuntimeError("DeathByCaptcha: Error report failed reCaptcha.")

        # ------------------------------------------------------------------------------- #

    def requestJob(self, jobID):
        if not jobID:
            raise RuntimeError("DeathByCaptcha: Error bad job id to request reCaptcha.")

        def _checkRequest(response):
            if response.status_code in [200, 303] and response.json().get('text'):
                return response

            self.checkErrorStatus(response)

            return None

        response = polling.poll(
            lambda: self.session.get(
                '{}/captcha/{}'.format(self.host, jobID),
                headers={'Accept': 'application/json'}
            ),
            check_success=_checkRequest,
            step=10,
            timeout=180
        )

        if response:
            return response.json().get('text')
        else:
            raise RuntimeError("DeathByCaptcha: Error failed to solve reCaptcha.")

        # ------------------------------------------------------------------------------- #

    def requestSolve(self, site_url, site_key):
        def _checkRequest(response):
            if response.status_code in [200, 303] and response.json().get("is_correct") and response.json().get('captcha'):
                return response

            self.checkErrorStatus(response)

            return None

        response = polling.poll(
            lambda: self.session.post(
                '{}/captcha'.format(self.host),
                headers={'Accept': 'application/json'},
                data={
                    'username': self.username,
                    'password': self.password,
                    'type': '4',
                    'token_params': json.dumps({
                        'googlekey': site_key,
                        'pageurl': site_url
                    })
                },
                allow_redirects=False
            ),
            check_success=_checkRequest,
            step=10,
            timeout=180
        )

        if response:
            return response.json().get('captcha')
        else:
            raise RuntimeError('DeathByCaptcha: Error no job id was returned.')

        # ------------------------------------------------------------------------------- #

    def getCaptchaAnswer(self, site_url, site_key, reCaptchaParams):
        jobID = None

        for param in ['username', 'password']:
            if not reCaptchaParams.get(param):
                raise ValueError("DeathByCaptcha: Missing '{}' parameter.".format(param))
            setattr(self, param, reCaptchaParams.get(param))

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
                raise RuntimeError("DeathByCaptcha: reCaptcha solve took to long and also failed reporting the job.")

            raise RuntimeError("DeathByCaptcha: reCaptcha solve took to long to execute, aborting.")


# ------------------------------------------------------------------------------- #

captchaSolver()
