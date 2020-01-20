# ------------------------------------------------------------------------------- #


class reCaptchaServiceUnavailable(Exception):
    """
    Raise error for external services that cannot be reached
    """


class reCaptchaErrorFromAPI(Exception):
    """
    Raise error for error from API response.
    """


class reCaptchaAccountError(Exception):
    """
    Raise error for reCaptcha provider account problem.
    """


class reCaptchaTimeout(Exception):
    """
    Raise error for reCaptcha provider taking too long.
    """


class reCaptchaBadParameter(Exception):
    """
    Raise error for bad or missing Parameter.
    """


class reCaptchaBadJobID(Exception):
    """
    Raise error for invalid job id.
    """


class reCaptchaReportError(Exception):
    """
    Raise error for reCaptcha provider unable to report bad solve.
    """


class reCaptchaImportError(Exception):
    """
    Raise error for reCaptcha, cannot import a module.
    """
