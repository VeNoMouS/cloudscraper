# -*- coding: utf-8 -*-
import hashlib
import responses

from os import path
from io import open

try:
    from urlparse import parse_qsl
except ImportError:
    from urllib.parse import parse_qsl

# Fake URL, network requests are not allowed by default when using the decorator
url = 'http://www.evildomain.com'

# These kwargs will be passed to tests by the decorator
cloudscraper_kwargs = dict(delay=0.01, debug=False)

# Cloudflare challenge fixtures are only read from the FS once
cache = {}

# ------------------------------------------------------------------------------- #


def fixtures(filename):
    """
    Read and cache a challenge fixture

    Returns: HTML (bytes): The HTML challenge fixture
    """
    if not cache.get(filename):
        print('reading...')
        with open(path.join(path.dirname(__file__), 'fixtures', filename), 'r') as fp:
            cache[filename] = fp.read()
    return cache[filename]

# ------------------------------------------------------------------------------- #


def mockCloudflare(fixture, payload):
    def responses_decorator(test):
        @responses.activate
        def wrapper(self):
            def post_callback(request):
                postPayload = dict(parse_qsl(request.body))
                postPayload['r'] = hashlib.sha256(postPayload.get('r', '').encode('ascii')).hexdigest()

                for param in payload:
                    if param not in postPayload or postPayload[param] != payload[param]:
                        return (
                            503,
                            {'Server': 'cloudflare'},
                            fixtures(fixture)
                        )

                # ------------------------------------------------------------------------------- #

                return (
                    200,
                    [
                        (
                            'Set-Cookie', '__cfduid=d5927a7cbaa96ec536939f93648e3c08a1576098703; Domain=.evildomain.com; path=/'
                        ),
                        (
                            'Set-Cookie',
                            '__cfduid=d5927a7cbaa96ec536939f93648e3c08a1576098703; domain=.evildomain.com; path=/'
                        ),
                        ('Server', 'cloudflare')
                    ],
                    'Solved OK'
                )

            # ------------------------------------------------------------------------------- #

            def challengeCallback(request):
                status_code = 503

                if 'reCaptcha' in fixture or '1020' in fixture:
                    status_code = 403
                return (
                    status_code,
                    [
                        (
                            'Set-Cookie',
                            '__cfduid=d5927a7cbaa96ec536939f93648e3c08a1576098703; Domain=.evildomain.com; path=/'
                        ),
                        ('Server', 'cloudflare')
                    ],
                    fixtures(fixture)
                )

            # ------------------------------------------------------------------------------- #

            responses.add_callback(
                responses.POST,
                url,
                callback=post_callback,
                content_type='text/html',
            )

            responses.add_callback(
                responses.GET,
                url,
                callback=challengeCallback,
                content_type='text/html',
            )

            # ------------------------------------------------------------------------------- #

            return test(self, **cloudscraper_kwargs)

        # ------------------------------------------------------------------------------- #

        return wrapper

    # ------------------------------------------------------------------------------- #

    return responses_decorator
