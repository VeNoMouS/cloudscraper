# -*- coding: utf-8 -*-
"""
cloudscraper.constants
======================

This module contains all constants used throughout cloudscraper.

Constants:
    - TLS versions and cipher suites
    - Timeouts and delays
    - Challenge detection patterns
    - Cookie names
    - HTTP status codes
"""

from __future__ import annotations

import ssl
from typing import Dict, List, Final

# -------------------------------------------------------------------------------
# TLS/SSL Constants
# -------------------------------------------------------------------------------

TLS_MIN_VERSION: Final[int] = ssl.TLSVersion.TLSv1_2
TLS_MAX_VERSION: Final[int] = ssl.TLSVersion.TLSv1_3
DEFAULT_ECDH_CURVE: Final[str] = 'prime256v1'

# -------------------------------------------------------------------------------
# Timeout and Delay Constants
# -------------------------------------------------------------------------------

DEFAULT_REQUEST_DELAY: Final[float] = 5.0
DEFAULT_MIN_REQUEST_INTERVAL: Final[float] = 1.0
DEFAULT_SESSION_REFRESH_INTERVAL: Final[int] = 3600  # 1 hour
DEFAULT_MAX_403_RETRIES: Final[int] = 3
DEFAULT_MAX_CONCURRENT_REQUESTS: Final[int] = 1
DEFAULT_BAN_TIME: Final[int] = 300  # 5 minutes
DEFAULT_SOLVE_DEPTH: Final[int] = 3
DEFAULT_REQUEST_TIMEOUT: Final[int] = 30

# -------------------------------------------------------------------------------
# HTTP Status Codes
# -------------------------------------------------------------------------------

CLOUDFLARE_CHALLENGE_STATUS_CODES: Final[List[int]] = [403, 429, 503]
RETRY_STATUS_CODES: Final[List[int]] = [429, 503]

# -------------------------------------------------------------------------------
# Cloudflare Cookie Names
# -------------------------------------------------------------------------------

CLOUDFLARE_COOKIE_NAMES: Final[List[str]] = [
    'cf_clearance',
    'cf_chl_2',
    'cf_chl_prog',
    'cf_chl_rc_ni',
    'cf_turnstile',
    '__cf_bm',
    '__cfduid'
]

# -------------------------------------------------------------------------------
# Challenge Detection Patterns (pre-compiled)
# -------------------------------------------------------------------------------

# Server header pattern
CLOUDFLARE_SERVER_PATTERN: Final[str] = r'^cloudflare$'

# Challenge form patterns
CHALLENGE_FORM_PATTERN: Final[str] = r'''<form .*?="challenge-form" action="/\S+__cf_chl_f_tk='''
NEW_CF_CHALLENGE_PATTERN: Final[str] = r'cpo.src\s*=\s*[\'"]/cdn-cgi/challenge-platform/\S+orchestrate/jsch/v1'
NEW_CF_CAPTCHA_PATTERN: Final[str] = r'cpo.src\s*=\s*[\'"]/cdn-cgi/challenge-platform/\S+orchestrate/(captcha|managed)/v1'
V3_CHALLENGE_PATTERN: Final[str] = r'cpo\.src\s*=\s*[\'"]/cdn-cgi/challenge-platform/\S+orchestrate/jsch/v3'
V3_CTX_PATTERN: Final[str] = r'window\._cf_chl_ctx\s*='
V3_FORM_PATTERN: Final[str] = r'<form[^>]*id="challenge-form"[^>]*action="[^"]*__cf_chl_rt_tk='
TURNSTILE_PATTERN: Final[str] = r'class="cf-turnstile"'
TURNSTILE_API_PATTERN: Final[str] = r'src="https://challenges.cloudflare.com/turnstile/v0/api.js'
TURNSTILE_SITEKEY_PATTERN: Final[str] = r'data-sitekey="[0-9A-Za-z]{40}"'
CAPTCHA_TRACE_PATTERN: Final[str] = r'/cdn-cgi/images/trace/(captcha|managed)/'
JSCH_TRACE_PATTERN: Final[str] = r'/cdn-cgi/images/trace/jsch/'
CF_ERROR_1020_PATTERN: Final[str] = r'<span class="cf-error-code">1020</span>'

# -------------------------------------------------------------------------------
# Proxy Rotation Strategies
# -------------------------------------------------------------------------------

PROXY_ROTATION_STRATEGIES: Final[Dict[str, str]] = {
    'sequential': 'sequential',
    'random': 'random',
    'smart': 'smart'
}

# -------------------------------------------------------------------------------
# Default Browser Configurations
# -------------------------------------------------------------------------------

DEFAULT_BROWSER: Final[str] = 'chrome'
DEFAULT_INTERPRETER: Final[str] = 'js2py'

# -------------------------------------------------------------------------------
# OpenSSL Version Check
# -------------------------------------------------------------------------------

MIN_OPENSSL_VERSION: Final[tuple] = (1, 1, 1)
OPENSSL_VERSION_INFO: Final[tuple] = ssl.OPENSSL_VERSION_INFO
IS_OPENSSL_SUPPORTED: Final[bool] = OPENSSL_VERSION_INFO >= MIN_OPENSSL_VERSION
