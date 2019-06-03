cloudscraper
=================
[![PyPI version](https://badge.fury.io/py/cloudscraper.svg)](https://badge.fury.io/py/cloudscraper)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![image](https://img.shields.io/pypi/pyversions/cloudscraper.svg)](https://pypi.org/project/cloudscraper/)
[![Build Status](https://travis-ci.com/VeNoMouS/cloudscraper.svg?branch=master)](https://travis-ci.com/VeNoMouS/cloudscraper)

A simple Python module to bypass Cloudflare's anti-bot page (also known as "I'm Under Attack Mode", or IUAM), implemented with [Requests](https://github.com/kennethreitz/requests). Cloudflare changes their techniques periodically, so I will update this repo frequently.

This can be useful if you wish to scrape or crawl a website protected with Cloudflare. Cloudflare's anti-bot page currently just checks if the client supports Javascript, though they may add additional techniques in the future.

Due to Cloudflare continually changing and hardening their protection page, cloudscraper requires a JavaScript interpreter to solve Javascript challenges. This allows the script to easily impersonate a regular web browser without explicitly deobfuscating and parsing Cloudflare's Javascript.

For reference, this is the default message Cloudflare uses for these sorts of pages:

    Checking your browser before accessing website.com.

    This process is automatic. Your browser will redirect to your requested content shortly.

    Please allow up to 5 seconds...

Any script using cloudscraper will sleep for ~5 seconds for the first visit to any site with Cloudflare anti-bots enabled, though no delay will occur after the first request.

Installation
============

Simply run `pip install cloudscraper`. The PyPI package is at https://pypi.python.org/pypi/cloudscraper/

Alternatively, clone this repository and run `python setup.py install`.

Dependencies
============

* Python 2.7 - 3.x
* **[Requests](https://github.com/kennethreitz/requests)** >= 2.9.2
* **[pyOpenSSL](https://pypi.org/project/pyOpenSSL/)** >= 17.0
* **[Brotli](https://pypi.org/project/Brotli/)** >= 1.0.7
* **[requests_toolbelt](https://pypi.org/project/requests-toolbelt/)** >= 0.9.1

Have the ability to choose between Javascript Interpreters.
* **[js2py](https://github.com/PiotrDabkowski/Js2Py)** >=0.60
* **[ChakraCore](https://github.com/microsoft/ChakraCore)**
  - Library binaries can also be located [here](https://www.github.com/VeNoMouS/cloudscraper/tree/ChakraCore/).
* **[V8](https://v8.dev)**
  - We use the python [v8eval](https://github.com/sony/v8eval/) module by Sony, which takes a billion years (~90 minutes) to compile and install V8.
* **[Node.js](https://nodejs.org/)**


`python setup.py install` will install the Python dependencies automatically. The javascript interpreters you decide to use are the only things you need to install yourself excluding js2py.

Updates
=======

Cloudflare modifies their anti-bot protection page occasionally, So far it has changed maybe once per year on average.

If you notice that the anti-bot page has changed, or if this module suddenly stops working, please create a GitHub issue so that I can update the code accordingly.

* Many issues are a result of users not updating to the latest release of this project. Before filing an issue, please run the following command:
```
pip show cloudscraper
```
If the value of the version field is not the latest release, please run the following to update your package:
```
pip install cloudscraper -U
```
If you are still encountering a problem, open an issue and please include:

* The full exception and stack trace.
* The URL of the Cloudflare-protected page which the script does not work on.
* A Pastebin or Gist containing the HTML source of the protected page.
* The version number from `pip show cloudscraper`.

Usage
=====

The simplest way to use cloudscraper is by calling `create_scraper()`.

```python
import cloudscraper

scraper = cloudscraper.create_scraper()  # returns a CloudScraper instance
# Or: scraper = cloudscraper.CloudScraper()  # CloudScraper inherits from requests.Session
print scraper.get("http://somesite.com").content  # => "<!DOCTYPE html><html><head>..."
```

That's it...

Any requests made from this session object to websites protected by Cloudflare anti-bot will be handled automatically. Websites not using Cloudflare will be treated normally. You don't need to configure or call anything further, and you can effectively treat all websites as if they're not protected with anything.

You use cloudscraper exactly the same way you use Requests. `CloudScraper` works identically to a Requests `Session` object, just instead of calling `requests.get()` or `requests.post()`, you call `scraper.get()` or `scraper.post()`.

Consult [Requests' documentation](http://docs.python-requests.org/en/latest/user/quickstart/) for more information.

## Options

### Existing session

If you already have an existing Requests session, you can pass it to `create_scraper()` to continue using that session.

```python
session = requests.session()
scraper = cloudscraper.create_scraper(sess=session)
```
Unfortunately, not all of Requests' session attributes are easily transferable, so if you run into problems with this, you should replace your initial `sess = requests.session()` call with `sess = cloudscraper.create_scraper()`.

--------------------------------------------------------------------------------

### Debug

```python
scraper = cloudscraper.create_scraper(debug=True)
```

Or

```python
scraper = cloudscraper.create_scraper()
scraper.debug = True
```
--------------------------------------------------------------------------------
### Delays

Normally, when a browser is faced with a Cloudflare IUAM challenge page, Cloudflare requires the browser to wait ~5 seconds before submitting the challenge answer. If a website is under heavy load, sometimes this may fail. One solution is to increase the delay (perhaps to 10 or 15 seconds, depending on the website). If you would like to override this delay, pass the `delay` keyword argument to `create_scraper()` or `CloudScraper()`.

There is no need to override this delay unless cloudscraper generates an error recommending you increase the delay.

```python
scraper = cloudscraper.create_scraper(delay=10)
```
or

```python
scraper = cloudscraper.create_scraper()
scraper.delay = 10
```
--------------------------------------------------------------------------------

### JavaScript Interpreters

Cloudscraper currently supports the following JavaScript Interpreters

* **[js2py](https://github.com/PiotrDabkowski/Js2Py)**
* **[Node.js](https://nodejs.org/)**
* **[ChakraCore](https://github.com/microsoft/ChakraCore)**
* **[V8](https://github.com/sony/v8eval/)**

The default interpreter is set to `js2py`,  you can set which to use by defining the `interpreter` parameter with one of the following values `js2py`, `nodejs`, `chakracore` or `v8`.

```python
scraper = cloudscraper.create_scraper(interpreter='nodejs')
```

or

```python
scraper = cloudscraper.create_scraper()
scraper.interpreter = 'nodejs'
```
--------------------------------------------------------------------------------

### 3rd Party reCaptcha Solvers

Cloudscraper currently supports the following 3rd party reCaptcha solvers, should you requiure them (but you shouldn't, unless you your doing something out of the norm).

* **[anticaptcha](https://www.anti-captcha.com/)**
* **[deathbycaptcha](https://www.deathbycaptcha.com/)**

I am working on adding more, so if you wish to have a service added, please raise a support ticket on github
#### anticaptcha

```python
scraper = cloudscraper.create_scraper(
  interpreter='nodejs',
  recaptcha={
    'provider': 'anticaptcha',
    'api_key': 'your_anticaptcha_api_key'
  }
)
```

or

```python
scraper = cloudscraper.create_scraper(interpreter='nodejs')
scraper.recaptcha={'provider': 'anticaptcha', 'api_key': 'your_anticaptcha_api_key'}
```

#### deathbycaptcha
```python
scraper = cloudscraper.create_scraper(
  interpreter='nodejs',
  recaptcha={
    'provider': 'deathbycaptcha',
    'username': 'your_deathbycaptcha_username',
    'password': 'your_deathbycaptcha_password',
  }
)
```

or

```python
scraper = cloudscraper.create_scraper(interpreter='nodejs')
scraper.recaptcha={
  'provider': 'deathbycaptcha',
  'username': 'your_deathbycaptcha_username',
  'password': 'your_deathbycaptcha_password'
}
```

##### * Note: if using a proxy and you wish to solve reCaptcha to the 3rd party via the proxy, pass `'proxy': True` in your `recaptcha` dictionary, it will use the scraper session proxy you set, otherwise it will use your default route.

--------------------------------------------------------------------------------

### Brotli Support

We have added in [Brotli](https://en.wikipedia.org/wiki/Brotli) decompression support in, and it is enabled by default, the __only__ way to disable it, is by passing the `allow_brotli` parameter set to`False` to `create_scraper()`

```python
scraper = cloudscraper.create_scraper(allow_brotli=False)
```

## Integration

It's easy to integrate cloudscraper with other applications and tools. Cloudflare uses two cookies as tokens: one to verify you made it past their challenge page and one to track your session. To bypass the challenge page, simply include both of these cookies (with the appropriate user-agent) in all HTTP requests you make.

To retrieve just the cookies (as a dictionary), use `cloudscraper.get_tokens()`. To retrieve them as a full `Cookie` HTTP header, use `cloudscraper.get_cookie_string()`.

`get_tokens` and `get_cookie_string` both accept Requests' usual keyword arguments (like `get_tokens(url, proxies={"http": "socks5://localhost:9050"})`).

Please read [Requests' documentation on request arguments](http://docs.python-requests.org/en/master/api/#requests.Session.request) for more information.

--------------------------------------------------------------------------------

### User-Agent Handling

The two integration functions return a tuple of `(cookie, user_agent_string)`.

**You must use the same user-agent string for obtaining tokens and for making requests with those tokens, otherwise Cloudflare will flag you as a bot.**

That means you have to pass the returned `user_agent_string` to whatever script, tool, or service you are passing the tokens to (e.g. curl, or a specialized scraping tool), and it must use that passed user-agent when it makes HTTP requests.

--------------------------------------------------------------------------------

### Integration examples

Remember, you must always use the same user-agent when retrieving or using these cookies. These functions all return a tuple of `(cookie_dict, user_agent_string)`.

--------------------------------------------------------------------------------

#### Retrieving a cookie dict through a proxy

`get_tokens` is a convenience function for returning a Python dict containing Cloudflare's session cookies. For demonstration, we will configure this request to use a proxy. (Please note that if you request Cloudflare clearance tokens through a proxy, you must always use the same proxy when those tokens are passed to the server. Cloudflare requires that the challenge-solving IP and the visitor IP stay the same.)

If you do not wish to use a proxy, just don't pass the `proxies` keyword argument. These convenience functions support all of Requests' normal keyword arguments, like `params`, `data`, and `headers`.

```python
import cloudscraper

proxies = {"http": "http://localhost:8080", "https": "http://localhost:8080"}
tokens, user_agent = cloudscraper.get_tokens("http://somesite.com", proxies=proxies)
print tokens
# => {
         'cf_clearance': 'c8f913c707b818b47aa328d81cab57c349b1eee5-1426733163-3600',
         '__cfduid': 'dd8ec03dfdbcb8c2ea63e920f1335c1001426733158'
     }
```
--------------------------------------------------------------------------------

#### Retrieving a cookie string

`get_cookie_string` is a convenience function for returning the tokens as a string for use as a `Cookie` HTTP header value.

This is useful when crafting an HTTP request manually, or working with an external application or library that passes on raw cookie headers.

```python
import cloudscraper

cookie_value, user_agent = cloudscraper.get_cookie_string('http://somesite.com')

print 'GET / HTTP/1.1\r\nCookie: {}\r\nUser-Agent: {}\r\n'.format(cookie_value, user_agent)

# GET / HTTP/1.1\r\n
# Cookie: cf_clearance=c8f913c707b818b47aa328d81cab57c349b1eee5-1426733163-3600; __cfduid=dd8ec03dfdbcb8c2ea63e920f1335c1001426733158
# User-Agent: Some/User-Agent String
```
--------------------------------------------------------------------------------

#### curl example

Here is an example of integrating cloudscraper with curl. As you can see, all you have to do is pass the cookies and user-agent to curl.

```python
import subprocess
import cloudscraper

# With get_tokens() cookie dict:

# tokens, user_agent = cloudscraper.get_tokens("http://somesite.com")
# cookie_arg = 'cf_clearance={}; __cfduid={}'.format(tokens['cf_clearance'], tokens['__cfduid'])

# With get_cookie_string() cookie header; recommended for curl and similar external applications:

cookie_arg, user_agent = cloudscraper.get_cookie_string('http://somesite.com')

# With a custom user-agent string you can optionally provide:

# ua = "Scraping Bot"
# cookie_arg, user_agent = cloudscraper.get_cookie_string("http://somesite.com", user_agent=ua)

result = subprocess.check_output(
    [
        'curl',
        '--cookie',
        cookie_arg,
        '-A',
        user_agent,
        'http://somesite.com'
    ]
)
```

Trimmed down version. Prints page contents of any site protected with Cloudflare, via curl.

**Warning: `shell=True` can be dangerous to use with `subprocess` in real code.**

```python
url = "http://somesite.com"
cookie_arg, user_agent = cloudscraper.get_cookie_string(url)
cmd = "curl --cookie {cookie_arg} -A {user_agent} {url}"
print(
    subprocess.check_output(
        cmd.format(
            cookie_arg=cookie_arg,
            user_agent=user_agent,
            url=url
        ),
        shell=True
    )
)
```
