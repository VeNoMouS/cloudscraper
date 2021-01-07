# -*- coding: utf-8 -*-

import pytest
import requests
import cloudscraper
import cloudscraper.help as helper

from collections import OrderedDict

from cloudscraper.exceptions import (
    CloudflareLoopProtection,
    CloudflareIUAMError,
    CloudflareCaptchaError,
    CloudflareCaptchaProvider,
    CaptchaParameter
)

from . import url, mockCloudflare


class TestCloudScraper:

    # ------------------------------------------------------------------------------- #

    @mockCloudflare(
        fixture='js_challenge-27-05-2020.html',
        payload=OrderedDict([
            ('jschl_answer', '102.7365930923'),
            ('pass', '1590526864.279-GCnY0hKdNH'),
            ('jschl_vc', '706241acd6cb287b270835d26b275f50'),
            ('r', 'b7f071b2f22b5dfecd144198317929d3f7c8d3d271c169e7676a42042c3581ed')
        ])
    )
    def test_js_challenge_27_05_2020(self, **kwargs):
        # test interpreters
        for interpreter in ['native', 'nodejs', 'js2py']:
            print('Testing {}'.format(interpreter))
            scraper = cloudscraper.create_scraper(interpreter=interpreter, **kwargs)
            scraper.get(url)

    # ------------------------------------------------------------------------------- #

    @mockCloudflare(
        fixture='js_challenge1_16_05_2020.html',
        payload=OrderedDict([
            ('jschl_answer', '-7.5155218172'),
            ('pass', '1589555973.262-n4Tt3w2mXt'),
            ('jschl_vc', 'df9d3a159bbde53c214e7abfcb005e0c'),
            ('r', 'f111bf7fe2d4d39d47dd837590808eeacb6e208a7503587f14a95c9ab0fc2d70')
        ])
    )
    def test_js_challenge1_16_05_2020(self, **kwargs):
        # test interpreters
        for interpreter in ['native', 'js2py', 'nodejs']:
            scraper = cloudscraper.create_scraper(interpreter=interpreter, **kwargs)
            scraper.get(url)

    # ------------------------------------------------------------------------------- #

    @mockCloudflare(
        fixture='js_challenge2_16_05_2020.html',
        payload=OrderedDict([
            ('jschl_answer', '58.4019148791'),
            ('pass', '1589581670.18-mkcsKJpz0a'),
            ('jschl_vc', 'ebec58fc1df89e2e403fa249469e50eb'),
            ('r', 'af028b8967c508037f3888dfaf85d403df9532f4ad851fea76c2ece4f4d9853b')
        ])
    )
    def test_js_challenge2_16_05_2020(self, **kwargs):
        # test interpreters
        for interpreter in ['native', 'js2py', 'nodejs']:
            scraper = cloudscraper.create_scraper(interpreter=interpreter, **kwargs)
            scraper.get(url)

    # ------------------------------------------------------------------------------- #

    def test_create_scraper_js_challenge1_16_05_2020(self, **kwargs):
        # test
        session = requests.session()
        session.auth = ('user', 'test')
        cloudscraper.create_scraper(session)

    # ------------------------------------------------------------------------------- #

    @mockCloudflare(fixture='js_challenge1_16_05_2020.html', payload={})
    def test_bad_interpreter_js_challenge1_16_05_2020(self, **kwargs):
        # test bad interpreter
        with pytest.raises(
            CloudflareIUAMError,
            match=r"Unable to parse Cloudflare anti-bots page: No module named*?"
        ):
            scraper = cloudscraper.create_scraper(interpreter='badInterpreter', **kwargs)
            scraper.get(url)

    # ------------------------------------------------------------------------------- #

    @mockCloudflare(
        fixture='js_challenge1_16_05_2020.html',
        payload=OrderedDict([
            ('jschl_answer', 'NOPE'),
            ('pass', '1589555973.262-n4Tt3w2mXt'),
            ('jschl_vc', 'df9d3a159bbde53c214e7abfcb005e0c'),
            ('r', 'f111bf7fe2d4d39d47dd837590808eeacb6e208a7503587f14a95c9ab0fc2d70')
        ])
    )
    def test_bad_solve_js_challenge1_16_05_2020(self, **kwargs):
        # test bad solve loop protection.
        with pytest.raises(
            CloudflareLoopProtection,
            match=r".*?Loop Protection.*?"
        ):
            scraper = cloudscraper.create_scraper(**kwargs)
            scraper.get(url)

    # ------------------------------------------------------------------------------- #

    def test_bad_js_challenge1_16_05_2020(self, **kwargs):
        # test bad Captcha extraction.
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
    def test_Captcha_challenge_12_12_2019(self, **kwargs):
        # test bad reCaptcha detection.
        with pytest.raises(
            CloudflareCaptchaProvider,
            match=r".*?Captcha detected*?"
        ):
            scraper = cloudscraper.create_scraper(**kwargs)
            scraper.get(url)

        scraper = cloudscraper.create_scraper(captcha={'provider': 'return_response'}, **kwargs)
        scraper.get(url)

    # ------------------------------------------------------------------------------- #

    def test_bad_reCaptcha_challenge_12_12_2019(self, **kwargs):
        # test bad reCaptcha extraction.
        with pytest.raises(
            CloudflareCaptchaError,
            match=r".*?we can't extract the parameters correctly.*?"
        ):
            scraper = cloudscraper.create_scraper(**kwargs)
            scraper.captcha_Challenge_Response(None, None, '', '')

    # ------------------------------------------------------------------------------- #

    @mockCloudflare(
        fixture='js_challenge1_16_05_2020.html',
        payload=OrderedDict([
            ('jschl_answer', '-7.5155218172'),
            ('pass', '1589555973.262-n4Tt3w2mXt'),
            ('jschl_vc', 'df9d3a159bbde53c214e7abfcb005e0c'),
            ('r', 'f111bf7fe2d4d39d47dd837590808eeacb6e208a7503587f14a95c9ab0fc2d70')
        ])
    )
    def test_getCookieString_challenge_js_challenge1_16_05_2020(self, **kwargs):
        scraper = cloudscraper.create_scraper(delay=0.1)
        assert '__cfduid' in scraper.get_cookie_string(url)[0]

    # ------------------------------------------------------------------------------- #

    def test_user_agent(self, **kwargs):
        for browser in ['chrome', 'firefox']:
            scraper = cloudscraper.create_scraper(browser={'browser': browser, 'platform': 'windows'}, delay=0.1)
            assert browser in scraper.headers['User-Agent'].lower()

        # Check it can't find browsers.json
        with pytest.raises(RuntimeError, match=r"Sorry \"bad_match\" browser is not valid.*?"):
            scraper = cloudscraper.create_scraper(browser='bad_match', delay=0.1)

        # Check mobile and desktop disabled
        with pytest.raises(
            RuntimeError,
            match=r"Sorry you can't have mobile and desktop disabled at the same time\."
        ):
            scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'desktop': False, 'mobile': False}, delay=0.1)

        # check brotli
        scraper = cloudscraper.create_scraper(browser='chrome', allow_brotli=False, delay=0.1)
        assert 'br' not in scraper.headers['Accept-Encoding']

        # test custom  User-Agent
        scraper = cloudscraper.create_scraper(browser={'custom': 'test'}, delay=0.1)
        assert scraper.headers['User-Agent'] == 'test'

        # check its matched chrome and loaded correct cipherSuite
        scraper = cloudscraper.create_scraper(browser={'custom': '50.0.9370.394', 'tryMatchCustom': True}, delay=0.1)
        assert any('!' not in _ for _ in scraper.user_agent.cipherSuite)

        # check it didn't match anything and loaded custom cipherSuite
        scraper = cloudscraper.create_scraper(browser={'custom': 'aa50.0.9370.394', 'tryMatchCustom': True}, delay=0.1)
        assert any('!' in _ for _ in scraper.user_agent.cipherSuite)

    # ------------------------------------------------------------------------------- #
    # test ReCaptcha

    @mockCloudflare(fixture='reCaptcha_challenge_12_12_2019.html', payload={})
    def test_reCaptcha_providers(self, **kwargs):
        for provider in ['9kw', '2captcha', 'anticaptcha', 'deathbycaptcha']:
            with pytest.raises(
                (CaptchaParameter, ImportError, CloudflareCaptchaError),
                match=r".*?: Missing .*? parameter\.|Please install.*?|Cloudflare Captcha detected.*?"
            ):
                scraper = cloudscraper.create_scraper(
                    captcha={
                        'provider': provider
                    },
                    delay=0.1
                )
                scraper.get(url)

    # ------------------------------------------------------------------------------- #
    # test BFM detection

    @mockCloudflare(fixture='bfm_07_01_2021.html', payload={})
    def test_bfm_07_01_2021(self, **kwargs):
        scraper = cloudscraper.create_scraper(delay=0.1)
        assert scraper.is_BFM_Challenge(scraper.get(url))

    # ------------------------------------------------------------------------------- #
    # test no BFM detection

    @mockCloudflare(fixture='js_challenge-27-05-2020.html', payload={})
    def test_not_bfm_07_01_2021(self, **kwargs):
        scraper = cloudscraper.create_scraper(delay=0.1)
        assert not scraper.is_BFM_Challenge(scraper.get(url))

    # ------------------------------------------------------------------------------- #

    def test_helper(self, **kwargs):
        payload = helper.systemInfo()
        assert payload
