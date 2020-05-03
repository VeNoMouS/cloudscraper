# -*- coding: utf-8 -*-
from unittest import mock

import pytest
import requests
from requests.structures import CaseInsensitiveDict

import cloudscraper
import cloudscraper.help as helper

from collections import OrderedDict

from cloudscraper.exceptions import (
    CloudflareLoopProtection,
    CloudflareIUAMError,
    CloudflareReCaptchaError,
    CloudflareReCaptchaProvider,
    reCaptchaParameter
)

from . import url, mockCloudflare


class TestCloudScraper:

    # ------------------------------------------------------------------------------- #

    @mockCloudflare(
        fixture='js_challenge_11_12_2019.html',
        payload=OrderedDict([
            ('jschl_answer', '3.5249426769'),
            ('pass', '1576018743.336-JjFrWpzMgq'),
            ('jschl_vc', '5770311b6edeca3c2fd42ad6921191bd'),
            ('r', '6a32cc8d8c61dc231ff47c3bcc8f24cbf7f7059d68ebcff4283ff3e15d73cca3')
        ])
    )
    def test_js_challenge_11_12_2019(self, **kwargs):
        # test interpreters
        for interpreter in ['native', 'js2py', 'nodejs']:
            scraper = cloudscraper.create_scraper(interpreter=interpreter, **kwargs)
            scraper.get(url)

    # ------------------------------------------------------------------------------- #

    def test_create_scraper_js_challenge_11_12_2019(self, **kwargs):
        # test
        session = requests.session()
        session.auth = ('user', 'test')
        cloudscraper.create_scraper(session)

    # ------------------------------------------------------------------------------- #

    @mockCloudflare(fixture='js_challenge_11_12_2019.html', payload={})
    def test_bad_interpreter_js_challenge_11_12_2019(self, **kwargs):
        # test bad interpreter
        with pytest.raises(
                CloudflareIUAMError,
                match=r"Unable to parse Cloudflare anti-bots page: No module named*?"
        ):
            scraper = cloudscraper.create_scraper(interpreter='badInterpreter', **kwargs)
            scraper.get(url)

    # ------------------------------------------------------------------------------- #

    @mockCloudflare(
        fixture='js_challenge_11_12_2019.html',
        payload=OrderedDict([
            ('jschl_answer', 'NOPE'),
            ('pass', '1576018743.336-JjFrWpzMgq'),
            ('jschl_vc', '5770311b6edeca3c2fd42ad6921191bd'),
            ('r', '6a32cc8d8c61dc231ff47c3bcc8f24cbf7f7059d68ebcff4283ff3e15d73cca3')
        ])
    )
    def test_bad_solve_js_challenge_11_12_2019(self, **kwargs):
        # test bad solve loop protection.
        with pytest.raises(
                CloudflareLoopProtection,
                match=r".*?Loop Protection.*?"
        ):
            scraper = cloudscraper.create_scraper(**kwargs)
            scraper.get(url)

    # ------------------------------------------------------------------------------- #

    def test_bad_js_challenge_12_12_2019(self, **kwargs):
        # test bad reCaptcha extraction.
        with pytest.raises(
                CloudflareIUAMError,
                match=r".*?we can't extract the parameters correctly.*?"
        ):
            scraper = cloudscraper.create_scraper(**kwargs)
            scraper.IUAM_Challenge_Response('', '', '')

        with pytest.raises(
                CloudflareIUAMError,
                match=r"Cloudflare IUAM detected, unfortunately we can't extract the parameters correctly."
        ):
            scraper = cloudscraper.create_scraper(**kwargs)
            scraper.IUAM_Challenge_Response(
                'id="challenge-form" action="blaaaaah" r value="" jschl_vc value="" pass value=""',
                url,
                'native'
            )

    # ------------------------------------------------------------------------------- #

    @mockCloudflare(fixture='reCaptcha_challenge_12_12_2019.html', payload={})
    def test_reCaptcha_challenge_12_12_2019(self, **kwargs):
        # test bad reCaptcha detection.
        with pytest.raises(
                CloudflareReCaptchaProvider,
                match=r".*?reCaptcha detected*?"
        ):
            scraper = cloudscraper.create_scraper(**kwargs)
            scraper.get(url)

        scraper = cloudscraper.create_scraper(recaptcha={'provider': 'return_response'}, **kwargs)
        scraper.get(url)

    # ------------------------------------------------------------------------------- #

    def test_bad_reCaptcha_challenge_12_12_2019(self, **kwargs):
        # test bad reCaptcha extraction.
        with pytest.raises(
                CloudflareReCaptchaError,
                match=r".*?we can't extract the parameters correctly.*?"
        ):
            scraper = cloudscraper.create_scraper(**kwargs)
            scraper.reCaptcha_Challenge_Response(None, None, '', '')

    # ------------------------------------------------------------------------------- #

    @mockCloudflare(
        fixture='js_challenge_11_12_2019.html',
        payload=OrderedDict([
            ('jschl_answer', '3.5249426769'),
            ('pass', '1576018743.336-JjFrWpzMgq'),
            ('jschl_vc', '5770311b6edeca3c2fd42ad6921191bd'),
            ('r', '6a32cc8d8c61dc231ff47c3bcc8f24cbf7f7059d68ebcff4283ff3e15d73cca3')
        ])
    )
    def test_getCookieString_challenge_11_12_2019(self, **kwargs):
        scraper = cloudscraper.create_scraper(delay=0)
        assert '__cfduid' in scraper.get_cookie_string(url)[0]

    # ------------------------------------------------------------------------------- #

    def test_user_agent(self, **kwargs):
        for browser in ['chrome', 'firefox']:
            scraper = cloudscraper.create_scraper(browser=browser)
            assert browser in scraper.headers['User-Agent'].lower()

        # Check it can't find browsers.json
        with pytest.raises(RuntimeError, match=r".*?User-Agent was not found\."):
            scraper = cloudscraper.create_scraper(browser='bad_match')

        # Check mobile and desktop disabled
        with pytest.raises(
                RuntimeError,
                match=r"Sorry you can't have mobile and desktop disabled at the same time\."
        ):
            scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'desktop': False, 'mobile': False})

        # check brotli
        scraper = cloudscraper.create_scraper(browser='chrome', allow_brotli=False)
        assert 'br' not in scraper.headers['Accept-Encoding']

        # test custom  User-Agent
        scraper = cloudscraper.create_scraper(browser={'custom': 'test'})
        assert scraper.headers['User-Agent'] == 'test'

        # check its matched chrome and loaded correct cipherSuite
        scraper = cloudscraper.create_scraper(browser={'custom': '50.0.9370.394', 'tryMatchCustom': True})
        assert any('!' not in _ for _ in scraper.user_agent.cipherSuite)

        # check it didn't match anything and loaded custom cipherSuite
        scraper = cloudscraper.create_scraper(browser={'custom': 'aa50.0.9370.394', 'tryMatchCustom': True})
        assert any('!' in _ for _ in scraper.user_agent.cipherSuite)

    # ------------------------------------------------------------------------------- #
    # test ReCaptcha

    @mockCloudflare(fixture='reCaptcha_challenge_12_12_2019.html', payload={})
    def test_reCaptcha_providers(self, **kwargs):
        for provider in ['9kw', '2captcha', 'anticaptcha', 'deathbycaptcha']:
            with pytest.raises(
                    (reCaptchaParameter, ImportError, CloudflareReCaptchaError),
                    match=r".*?: Missing .*? parameter\.|Please install.*?|Cloudflare reCaptcha detected.*?"
            ):
                scraper = cloudscraper.create_scraper(
                    recaptcha={
                        'provider': provider
                    }
                )
                scraper.get(url)

    # ------------------------------------------------------------------------------- #

    def test_helper(self, **kwargs):
        payload = helper.systemInfo()
        assert payload

    def test_is_iuam_challenge(self):
        resp = requests.Response()
        dic = CaseInsensitiveDict()
        dic['Server'] = 'cloudflare'
        resp.headers = dic
        resp.status_code = 503
        with open('tests/fixtures/js_challenge_05-03-2020.html') as file:
            type(resp).text = mock.PropertyMock(return_value=file.read())

        assert cloudscraper.CloudScraper.is_IUAM_Challenge(resp)

        with open('tests/fixtures/js_challenge_11_12_2019.html') as file:
            type(resp).text = mock.PropertyMock(return_value=file.read())

        assert cloudscraper.CloudScraper.is_IUAM_Challenge(resp)

        resp.status_code = 429
        assert cloudscraper.CloudScraper.is_IUAM_Challenge(resp)

        resp.status_code = 404
        assert not cloudscraper.CloudScraper.is_IUAM_Challenge(resp)

        resp.status_code = 200
        assert not cloudscraper.CloudScraper.is_IUAM_Challenge(resp)

        resp.status_code = 503
        dic['Server'] = ''
        assert not cloudscraper.CloudScraper.is_IUAM_Challenge(resp)


