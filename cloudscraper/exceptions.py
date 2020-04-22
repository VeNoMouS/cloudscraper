# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------- #

"""
cloudscraper.exceptions
~~~~~~~~~~~~~~~~~~~
This module contains the set of cloudscraper exceptions.
"""

# ------------------------------------------------------------------------------- #


class CloudflareException(Exception):
    """
    Base exception class for cloudscraper for Cloudflare
    """


class CloudflareLoopProtection(CloudflareException):
    """
    Raise an exception for recursive depth protection
    """


class CloudflareCode1020(CloudflareException):
    """
    Raise an exception for Cloudflare code 1020 block
    """


class CloudflareIUAMError(CloudflareException):
    """
    Raise an error for problem extracting IUAM paramters
    from Cloudflare payload
    """


class CloudflareChallengeError(CloudflareException):
    """
    Raise an error when detected new Cloudflare challenge
    """


class CloudflareSolveError(CloudflareException):
    """
    Raise an error when issue with solving Cloudflare challenge
    """


class CloudflareReCaptchaError(CloudflareException):
    """
    Raise an error for problem extracting reCaptcha paramters
    from Cloudflare payload
    """


class CloudflareReCaptchaProvider(CloudflareException):
    """
    Raise an exception for no reCaptcha provider loaded for Cloudflare.
    """

# ------------------------------------------------------------------------------- #


class reCaptchaException(Exception):
    """
    Base exception class for cloudscraper reCaptcha Providers
    """


class reCaptchaServiceUnavailable(reCaptchaException):
    """
    Raise an exception for external services that cannot be reached
    """


class reCaptchaAPIError(reCaptchaException):
    """
    Raise an error for error from API response.
    """


class reCaptchaAccountError(reCaptchaException):
    """
    Raise an error for reCaptcha provider account problem.
    """


class reCaptchaTimeout(reCaptchaException):
    """
    Raise an exception for reCaptcha provider taking too long.
    """


class reCaptchaParameter(reCaptchaException):
    """
    Raise an exception for bad or missing Parameter.
    """


class reCaptchaBadJobID(reCaptchaException):
    """
    Raise an exception for invalid job id.
    """


class reCaptchaReportError(reCaptchaException):
    """
    Raise an error for reCaptcha provider unable to report bad solve.
    """
