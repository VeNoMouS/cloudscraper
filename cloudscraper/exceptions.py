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


class CloudflareCaptchaError(CloudflareException):
    """
    Raise an error for problem extracting Captcha paramters
    from Cloudflare payload
    """


class CloudflareCaptchaProvider(CloudflareException):
    """
    Raise an exception for no Captcha provider loaded for Cloudflare.
    """

# ------------------------------------------------------------------------------- #


class CaptchaException(Exception):
    """
    Base exception class for cloudscraper captcha Providers
    """


class CaptchaServiceUnavailable(CaptchaException):
    """
    Raise an exception for external services that cannot be reached
    """


class CaptchaAPIError(CaptchaException):
    """
    Raise an error for error from API response.
    """


class CaptchaAccountError(CaptchaException):
    """
    Raise an error for captcha provider account problem.
    """


class CaptchaTimeout(CaptchaException):
    """
    Raise an exception for captcha provider taking too long.
    """


class CaptchaParameter(CaptchaException):
    """
    Raise an exception for bad or missing Parameter.
    """


class CaptchaBadJobID(CaptchaException):
    """
    Raise an exception for invalid job id.
    """


class CaptchaReportError(CaptchaException):
    """
    Raise an error for captcha provider unable to report bad solve.
    """
