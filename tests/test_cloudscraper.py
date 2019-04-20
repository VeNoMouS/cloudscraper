# -*- coding: utf-8 -*-

import pytest
import cloudscraper

from sure import expect
from . import challenge_responses, requested_page, url

delay = 0.01
debug = False


class TestCloudScraper:

    @challenge_responses(filename='js_challenge_10_04_2019.html', jschl_answer='18.8766915031')
    def test_js_challenge_10_04_2019(self, interpreter):
        if interpreter != 'js2py':
            scraper = cloudscraper.CloudScraper(delay=delay, debug=debug, interpreter=interpreter)
            expect(scraper.get(url).content).to.equal(requested_page)
        else:
            pytest.skip('js2py.internals.simplex.JsException: TypeError: \'undefined\' is not a function')

    @challenge_responses(filename='js_challenge_21_03_2019.html', jschl_answer='13.0802397598')
    def test_js_challenge_21_03_2019(self, interpreter):
        scraper = cloudscraper.CloudScraper(delay=delay, debug=debug, interpreter=interpreter)
        expect(scraper.get(url).content).to.equal(requested_page)

    @challenge_responses(filename='js_challenge_13_03_2019.html', jschl_answer='38.5879578333')
    def test_js_challenge_13_03_2019(self, interpreter):
        scraper = cloudscraper.CloudScraper(delay=delay, debug=debug, interpreter=interpreter)
        expect(scraper.get(url).content).to.equal(requested_page)

    @challenge_responses(filename='js_challenge_03_12_2018.html', jschl_answer='10.66734594')
    def test_js_challenge_03_12_2018(self, interpreter):
        scraper = cloudscraper.CloudScraper(delay=delay, debug=debug, interpreter=interpreter)
        expect(scraper.get(url).content).to.equal(requested_page)

    @challenge_responses(filename='js_challenge_09_06_2016.html', jschl_answer='6648')
    def test_js_challenge_09_06_2016(self, interpreter):
        scraper = cloudscraper.CloudScraper(delay=delay, debug=debug, interpreter=interpreter)
        expect(scraper.get(url).content).to.equal(requested_page)

    @pytest.mark.skip(reason='Unable to identify Cloudflare IUAM Javascript on website.')
    @challenge_responses(filename='js_challenge_21_05_2015.html', jschl_answer='649')
    def test_js_challenge_21_05_2015(self, interpreter):
        scraper = cloudscraper.CloudScraper(delay=delay, debug=debug, interpreter=interpreter)
        expect(scraper.get(url).content).to.equal(requested_page)
