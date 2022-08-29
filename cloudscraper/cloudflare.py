# Cloudflare V1

import re
import sys
import time

from copy import deepcopy
from collections import OrderedDict

# ------------------------------------------------------------------------------- #

try:
    from HTMLParser import HTMLParser
except ImportError:
    if sys.version_info >= (3, 4):
        import html
    else:
        from html.parser import HTMLParser

try:
    from urlparse import urlparse, urljoin
except ImportError:
    from urllib.parse import urlparse, urljoin

# ------------------------------------------------------------------------------- #

from .exceptions import (
    CloudflareCode1020,
    CloudflareIUAMError,
    CloudflareSolveError,
    CloudflareChallengeError,
    CloudflareCaptchaError,
    CloudflareCaptchaProvider
)

# ------------------------------------------------------------------------------- #

from .captcha import Captcha
from .interpreters import JavaScriptInterpreter

# ------------------------------------------------------------------------------- #


class Cloudflare():

    def __init__(self, cloudscraper):
        self.cloudscraper = cloudscraper

    # ------------------------------------------------------------------------------- #
    # Unescape / decode html entities
    # ------------------------------------------------------------------------------- #

    @staticmethod
    def unescape(html_text):
        if sys.version_info >= (3, 0):
            if sys.version_info >= (3, 4):
                return html.unescape(html_text)

            return HTMLParser().unescape(html_text)

        return HTMLParser().unescape(html_text)

    # ------------------------------------------------------------------------------- #
    # check if the response contains a valid Cloudflare challenge
    # ------------------------------------------------------------------------------- #

    @staticmethod
    def is_IUAM_Challenge(resp):
        try:
            return (
                resp.headers.get('Server', '').startswith('cloudflare')
                and resp.status_code in [429, 503]
                and re.search(r'/cdn-cgi/images/trace/jsch/', resp.text, re.M | re.S)
                and re.search(
                    r'''<form .*?="challenge-form" action="/\S+__cf_chl_f_tk=''',
                    resp.text,
                    re.M | re.S
                )
            )
        except AttributeError:
            pass

        return False

    # ------------------------------------------------------------------------------- #
    # check if the response contains new Cloudflare challenge
    # ------------------------------------------------------------------------------- #

    def is_New_IUAM_Challenge(self, resp):
        try:
            return (
                self.is_IUAM_Challenge(resp)
                and re.search(
                    r'''cpo.src\s*=\s*['"]/cdn-cgi/challenge-platform/\S+orchestrate/jsch/v1''',
                    resp.text,
                    re.M | re.S
                )
            )
        except AttributeError:
            pass

        return False

    # ------------------------------------------------------------------------------- #
    # check if the response contains a v2 hCaptcha Cloudflare challenge
    # ------------------------------------------------------------------------------- #

    def is_New_Captcha_Challenge(self, resp):
        try:
            return (
                self.is_Captcha_Challenge(resp)
                and re.search(
                    r'''cpo.src\s*=\s*['"]/cdn-cgi/challenge-platform/\S+orchestrate/(captcha|managed)/v1''',
                    resp.text,
                    re.M | re.S
                )
            )
        except AttributeError:
            pass

        return False

    # ------------------------------------------------------------------------------- #
    # check if the response contains a Cloudflare hCaptcha challenge
    # ------------------------------------------------------------------------------- #

    @staticmethod
    def is_Captcha_Challenge(resp):
        try:
            return (
                resp.headers.get('Server', '').startswith('cloudflare')
                and resp.status_code == 403
                and re.search(r'/cdn-cgi/images/trace/(captcha|managed)/', resp.text, re.M | re.S)
                and re.search(
                    r'''<form .*?="challenge-form" action="/\S+__cf_chl_f_tk=''',
                    resp.text,
                    re.M | re.S
                )
            )
        except AttributeError:
            pass

        return False

    # ------------------------------------------------------------------------------- #
    # check if the response contains Firewall 1020 Error
    # ------------------------------------------------------------------------------- #

    @staticmethod
    def is_Firewall_Blocked(resp):
        try:
            return (
                resp.headers.get('Server', '').startswith('cloudflare')
                and resp.status_code == 403
                and re.search(
                    r'<span class="cf-error-code">1020</span>',
                    resp.text,
                    re.M | re.DOTALL
                )
            )
        except AttributeError:
            pass

        return False

    # ------------------------------------------------------------------------------- #
    # Wrapper for is_Captcha_Challenge, is_IUAM_Challenge, is_Firewall_Blocked
    # ------------------------------------------------------------------------------- #

    def is_Challenge_Request(self, resp):
        if self.is_Firewall_Blocked(resp):
            self.cloudscraper.simpleException(
                CloudflareCode1020,
                'Cloudflare has blocked this request (Code 1020 Detected).'
            )

        if self.is_New_Captcha_Challenge(resp):
            self.cloudscraper.simpleException(
                CloudflareChallengeError,
                'Detected a Cloudflare version 2 Captcha challenge, This feature is not available in the opensource (free) version.'
            )

        if self.is_New_IUAM_Challenge(resp):
            self.cloudscraper.simpleException(
                CloudflareChallengeError,
                'Detected a Cloudflare version 2 challenge, This feature is not available in the opensource (free) version.'
            )

        if self.is_Captcha_Challenge(resp) or self.is_IUAM_Challenge(resp):
            if self.cloudscraper.debug:
                print('Detected a Cloudflare version 1 challenge.')
            return True

        return False

    # ------------------------------------------------------------------------------- #
    # Try to solve cloudflare javascript challenge.
    # ------------------------------------------------------------------------------- #

    def IUAM_Challenge_Response(self, body, url, interpreter):
        try:
            formPayload = re.search(
                r'<form (?P<form>.*?="challenge-form" '
                r'action="(?P<challengeUUID>.*?'
                r'__cf_chl_f_tk=\S+)"(.*?)</form>)',
                body,
                re.M | re.DOTALL
            ).groupdict()

            if not all(key in formPayload for key in ['form', 'challengeUUID']):
                self.cloudscraper.simpleException(
                    CloudflareIUAMError,
                    "Cloudflare IUAM detected, unfortunately we can't extract the parameters correctly."
                )

            payload = OrderedDict()
            for challengeParam in re.findall(r'^\s*<input\s(.*?)/>', formPayload['form'], re.M | re.S):
                inputPayload = dict(re.findall(r'(\S+)="(\S+)"', challengeParam))
                if inputPayload.get('name') in ['r', 'jschl_vc', 'pass']:
                    payload.update({inputPayload['name']: inputPayload['value']})

        except AttributeError:
            self.cloudscraper.simpleException(
                CloudflareIUAMError,
                "Cloudflare IUAM detected, unfortunately we can't extract the parameters correctly."
            )

        hostParsed = urlparse(url)

        try:
            payload['jschl_answer'] = JavaScriptInterpreter.dynamicImport(
                interpreter
            ).solveChallenge(body, hostParsed.netloc)
        except Exception as e:
            self.cloudscraper.simpleException(
                CloudflareIUAMError,
                f"Unable to parse Cloudflare anti-bots page: {getattr(e, 'message', e)}"
            )

        return {
            'url': f"{hostParsed.scheme}://{hostParsed.netloc}{self.unescape(formPayload['challengeUUID'])}",
            'data': payload
        }

    # ------------------------------------------------------------------------------- #
    #  Try to solve the Captcha challenge via 3rd party.
    # ------------------------------------------------------------------------------- #

    def captcha_Challenge_Response(self, provider, provider_params, body, url):
        try:
            formPayload = re.search(
                r'<form (?P<form>.*?="challenge-form" '
                r'action="(?P<challengeUUID>.*?__cf_chl_captcha_tk__=\S+)"(.*?)</form>)',
                body,
                re.M | re.DOTALL
            ).groupdict()

            if not all(key in formPayload for key in ['form', 'challengeUUID']):
                self.cloudscraper.simpleException(
                    CloudflareCaptchaError,
                    "Cloudflare Captcha detected, unfortunately we can't extract the parameters correctly."
                )

            payload = OrderedDict(
                re.findall(
                    r'(name="r"\svalue|data-ray|data-sitekey|name="cf_captcha_kind"\svalue)="(.*?)"',
                    formPayload['form']
                )
            )

            captchaType = 'reCaptcha' if payload['name="cf_captcha_kind" value'] == 're' else 'hCaptcha'

        except (AttributeError, KeyError):
            self.cloudscraper.simpleException(
                CloudflareCaptchaError,
                "Cloudflare Captcha detected, unfortunately we can't extract the parameters correctly."
            )

        # ------------------------------------------------------------------------------- #
        # Pass proxy parameter to provider to solve captcha.
        # ------------------------------------------------------------------------------- #

        if self.cloudscraper.proxies and self.cloudscraper.proxies != self.cloudscraper.captcha.get('proxy'):
            self.cloudscraper.captcha['proxy'] = self.proxies

        # ------------------------------------------------------------------------------- #
        # Pass User-Agent if provider supports it to solve captcha.
        # ------------------------------------------------------------------------------- #

        self.cloudscraper.captcha['User-Agent'] = self.cloudscraper.headers['User-Agent']

        # ------------------------------------------------------------------------------- #
        # Submit job to provider to request captcha solve.
        # ------------------------------------------------------------------------------- #

        captchaResponse = Captcha.dynamicImport(
            provider.lower()
        ).solveCaptcha(
            captchaType,
            url,
            payload['data-sitekey'],
            provider_params
        )

        # ------------------------------------------------------------------------------- #
        # Parse and handle the response of solved captcha.
        # ------------------------------------------------------------------------------- #

        dataPayload = OrderedDict([
            ('r', payload.get('name="r" value', '')),
            ('cf_captcha_kind', payload['name="cf_captcha_kind" value']),
            ('id', payload.get('data-ray')),
            ('g-recaptcha-response', captchaResponse)
        ])

        if captchaType == 'hCaptcha':
            dataPayload.update({'h-captcha-response': captchaResponse})

        hostParsed = urlparse(url)

        return {
            'url': f"{hostParsed.scheme}://{hostParsed.netloc}{self.unescape(formPayload['challengeUUID'])}",
            'data': dataPayload
        }

    # ------------------------------------------------------------------------------- #
    # Attempt to handle and send the challenge response back to cloudflare
    # ------------------------------------------------------------------------------- #

    def Challenge_Response(self, resp, **kwargs):
        if self.is_Captcha_Challenge(resp):
            # ------------------------------------------------------------------------------- #
            # double down on the request as some websites are only checking
            # if cfuid is populated before issuing Captcha.
            # ------------------------------------------------------------------------------- #

            if self.cloudscraper.doubleDown:
                resp = self.cloudscraper.decodeBrotli(
                    self.cloudscraper.perform_request(resp.request.method, resp.url, **kwargs)
                )

            if not self.is_Captcha_Challenge(resp):
                return resp

            # ------------------------------------------------------------------------------- #
            # if no captcha provider raise a runtime error.
            # ------------------------------------------------------------------------------- #

            if (
                not self.cloudscraper.captcha
                or not isinstance(self.cloudscraper.captcha, dict)
                or not self.cloudscraper.captcha.get('provider')
            ):
                self.cloudscraper.simpleException(
                    CloudflareCaptchaProvider,
                    "Cloudflare Captcha detected, unfortunately you haven't loaded an anti Captcha provider "
                    "correctly via the 'captcha' parameter."
                )

            # ------------------------------------------------------------------------------- #
            # if provider is return_response, return the response without doing anything.
            # ------------------------------------------------------------------------------- #

            if self.cloudscraper.captcha.get('provider') == 'return_response':
                return resp

            # ------------------------------------------------------------------------------- #
            # Submit request to parser wrapper to solve captcha
            # ------------------------------------------------------------------------------- #

            submit_url = self.captcha_Challenge_Response(
                self.cloudscraper.captcha.get('provider'),
                self.cloudscraper.captcha,
                resp.text,
                resp.url
            )
        else:
            # ------------------------------------------------------------------------------- #
            # Cloudflare requires a delay before solving the challenge
            # ------------------------------------------------------------------------------- #

            if not self.cloudscraper.delay:
                try:
                    delay = float(
                        re.search(
                            r'submit\(\);\r?\n\s*},\s*([0-9]+)',
                            resp.text
                        ).group(1)
                    ) / float(1000)
                    if isinstance(delay, (int, float)):
                        self.cloudscraper.delay = delay
                except (AttributeError, ValueError):
                    self.cloudscraper.simpleException(
                        CloudflareIUAMError,
                        "Cloudflare IUAM possibility malformed, issue extracing delay value."
                    )

            time.sleep(self.cloudscraper.delay)

            # ------------------------------------------------------------------------------- #

            submit_url = self.IUAM_Challenge_Response(
                resp.text,
                resp.url,
                self.cloudscraper.interpreter
            )

        # ------------------------------------------------------------------------------- #
        # Send the Challenge Response back to Cloudflare
        # ------------------------------------------------------------------------------- #

        if submit_url:

            def updateAttr(obj, name, newValue):
                try:
                    obj[name].update(newValue)
                    return obj[name]
                except (AttributeError, KeyError):
                    obj[name] = {}
                    obj[name].update(newValue)
                    return obj[name]

            cloudflare_kwargs = deepcopy(kwargs)
            cloudflare_kwargs['allow_redirects'] = False
            cloudflare_kwargs['data'] = updateAttr(
                cloudflare_kwargs,
                'data',
                submit_url['data']
            )

            urlParsed = urlparse(resp.url)
            cloudflare_kwargs['headers'] = updateAttr(
                cloudflare_kwargs,
                'headers',
                {
                    'Origin': f'{urlParsed.scheme}://{urlParsed.netloc}',
                    'Referer': resp.url
                }
            )

            challengeSubmitResponse = self.cloudscraper.request(
                'POST',
                submit_url['url'],
                **cloudflare_kwargs
            )

            if challengeSubmitResponse.status_code == 400:
                self.cloudscraper.simpleException(
                    CloudflareSolveError,
                    'Invalid challenge answer detected, Cloudflare broken?'
                )

            # ------------------------------------------------------------------------------- #
            # Return response if Cloudflare is doing content pass through instead of 3xx
            # else request with redirect URL also handle protocol scheme change http -> https
            # ------------------------------------------------------------------------------- #

            if not challengeSubmitResponse.is_redirect:
                return challengeSubmitResponse

            else:
                cloudflare_kwargs = deepcopy(kwargs)
                cloudflare_kwargs['headers'] = updateAttr(
                    cloudflare_kwargs,
                    'headers',
                    {'Referer': challengeSubmitResponse.url}
                )

                if not urlparse(challengeSubmitResponse.headers['Location']).netloc:
                    redirect_location = urljoin(
                        challengeSubmitResponse.url,
                        challengeSubmitResponse.headers['Location']
                    )
                else:
                    redirect_location = challengeSubmitResponse.headers['Location']

                return self.cloudscraper.request(
                    resp.request.method,
                    redirect_location,
                    **cloudflare_kwargs
                )

        # ------------------------------------------------------------------------------- #
        # We shouldn't be here...
        # Re-request the original query and/or process again....
        # ------------------------------------------------------------------------------- #

        return self.cloudscraper.request(resp.request.method, resp.url, **kwargs)

    # ------------------------------------------------------------------------------- #
