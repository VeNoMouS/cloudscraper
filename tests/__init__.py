# -*- coding: utf-8 -*-

import responses
import pytest
import re

from requests.compat import urlencode
from collections import OrderedDict
from os import path
from io import open

url = 'http://example-site.dev'
cache = {}


class ChallengeResponse(responses.Response):
    def __init__(self, **kwargs):
        kwargs = dict(
            method='GET',
            status=503,
            headers={'Server': 'cloudflare'},
            content_type='text/html',
            **kwargs
        )
        super(ChallengeResponse, self).__init__(**kwargs)


class RedirectResponse(responses.Response):
    def __init__(self, **kwargs):
        kwargs = dict(
            method='GET',
            status=302,
            content_type='text/html',
            headers={'Location': '/'},
            **kwargs
        )
        super(RedirectResponse, self).__init__(**kwargs)


class RequestedResponse(responses.Response):
    def __init__(self, **kwargs):
        kwargs = dict(
            method='GET',
            status=200,
            content_type='text/html',
            **kwargs
        )
        super(RequestedResponse, self).__init__(**kwargs)


def fixtures(filename):
    if not cache.get(filename):
        with open(path.join(path.dirname(__file__), 'fixtures', filename), 'rb') as fp:
            cache[filename] = fp.read()
    return cache[filename]


requested_page = fixtures('requested_page.html')


def challenge_responses(filename, jschl_answer):
    def challenge_responses_decorator(test):
        @responses.activate
        def wrapper(self, interpreter):
            html = fixtures(filename).decode('utf-8')

            params = OrderedDict()

            s = re.search(r'name="s"\svalue="(?P<s_value>[^"]+)', html)
            if s:
                params['s'] = s.group('s_value')
            params['jschl_vc'] = re.search(r'name="jschl_vc" value="(\w+)"', html).group(1)
            params['pass'] = re.search(r'name="pass" value="(.+?)"', html).group(1)
            params['jschl_answer'] = jschl_answer

            submit_uri = '{}/cdn-cgi/l/chk_jschl?{}'.format(url, urlencode(params))

            responses.add(ChallengeResponse(url=url, body=fixtures(filename)))
            responses.add(RedirectResponse(url=submit_uri))
            responses.add(RequestedResponse(url=url, body=requested_page))

            return test(self, interpreter)
        return pytest.mark.parametrize('interpreter', ['js2py', 'nodejs'])(wrapper)
    return challenge_responses_decorator
