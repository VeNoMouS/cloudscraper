# cloudscraper

[![Python](https://img.shields.io/badge/Made%20with-Python%203.10-blue.svg?style=flat-square&logo=Python&logoColor=white)](https://www.python.org/)
[![GitHub license](https://img.shields.io/github/license/curseforge-mirror/cloudscraper)](https://github.com/curseforge-mirror/cloudscraper/blob/main/LICENSE)
[![Recent Workflown Status](https://github.com/curseforge-mirror/cloudscraper/actions/workflows/ci.yml/badge.svg)](https://github.com/curseforge-mirror/cloudscraper/actions/workflows/ci.yml)

A simple Python module to bypass Cloudflare's anti-bot page (also known as "I'm Under Attack Mode", or IUAM), implemented with [Requests](https://github.com/kennethreitz/requests). Cloudflare changes their techniques periodically, so I will update this repo frequently.

This can be useful if you wish to scrape or crawl a website protected with Cloudflare. Cloudflare's anti-bot page currently just checks if the client supports Javascript, though they may add additional techniques in the future.

Due to Cloudflare continually changing and hardening their protection page, cloudscraper requires a JavaScript Engine/interpreter to solve Javascript challenges. This allows the script to easily impersonate a regular web browser without explicitly deobfuscating and parsing Cloudflare's Javascript.

For reference, this is the default message Cloudflare uses for these sorts of pages:

```
Checking your browser before accessing website.com.

This process is automatic. Your browser will redirect to your requested content shortly.

Please allow up to 5 seconds...
```

Any script using cloudscraper will sleep for ~5 seconds for the first visit to any site with Cloudflare anti-bots enabled, though no delay will occur after the first request.

# Installation

Simply run `pip install git+https://github.com/curseforge-mirror/cloudscraper#egg=cloudscraper`. The PyPI package is **NOT** this project and will not contain its fixes

Alternatively, clone this repository and run `python setup.py install`.

# Contributing
This repo is accepting contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for more info!

# Dependencies

- Python 3.10+ (though will run on non-EOL versions!)
- **[Requests](https://github.com/kennethreitz/requests)**
- **[requests_toolbelt](https://pypi.org/project/requests-toolbelt/)**

`python setup.py install` will install the Python dependencies automatically. The javascript interpreters and/or engines you decide to use are the only things you need to install yourself, excluding js2py which is part of the requirements as the default.

# Javascript Interpreters and Engines

We support the following Javascript interpreters/engines.

- **[js2py](https://github.com/PiotrDabkowski/Js2Py):** >=0.67
- **native**: Self made native python solver **(Default)**
- **[Node.js](https://nodejs.org/)**
- **[V8](https://github.com/sony/v8eval/):** We use Sony's [v8eval](https://v8.dev)() python module.

# Usage

The simplest way to use cloudscraper is by calling `create_scraper()`.

```python
import cloudscraper

scraper = cloudscraper.create_scraper()  # returns a CloudScraper instance
# Or: scraper = cloudscraper.CloudScraper()  # CloudScraper inherits from requests.Session
print(scraper.get("http://somesite.com").text)  # => "<!DOCTYPE html><html><head>..."
```

That's it...

Any requests made from this session object to websites protected by Cloudflare anti-bot will be handled automatically. Websites not using Cloudflare will be treated normally. You don't need to configure or call anything further, and you can effectively treat all websites as if they're not protected with anything.

You use cloudscraper exactly the same way you use Requests. `cloudScraper` works identically to a Requests `Session` object, just instead of calling `requests.get()` or `requests.post()`, you call `scraper.get()` or `scraper.post()`.

Consult [Requests' documentation](http://docs.python-requests.org/en/latest/user/quickstart/) for more information.

## Options

### Disable Cloudflare V1
#### Description

If you don't want to even attempt Cloudflare v1 (Deprecated) solving..

#### Parameters


|Parameter|Value|Default|
|-------------|:-------------:|:-----:|
|disableCloudflareV1|(boolean)|False|

#### Example

```python
scraper = cloudscraper.create_scraper(disableCloudflareV1=True)
```

------

### Brotli

#### Description

[Brotli](https://en.wikipedia.org/wiki/Brotli) decompression support has been added, and it is enabled by default.

#### Parameters


|Parameter|Value|Default|
|-------------|:-------------:|:-----:|
|allow_brotli|(boolean)|True|

#### Example

```python
scraper = cloudscraper.create_scraper(allow_brotli=False)
```

------

### Browser / User-Agent Filtering

#### Description

Control how and which User-Agent is "randomly" selected.

#### Parameters

Can be passed as an argument to `create_scraper()`, `get_tokens()`, `get_cookie_string()`.

|Parameter|Value|Default|
|-------------|:-------------:|:-----:|
|browser|(string) `chrome` or `firefox`|None|

Or

|Parameter|Value|Default|
|-------------|:-------------:|:-----:|
|browser|(dict)||

##### `browser` *_dict_* Parameters
|Parameter|Value|Default|
|-------------|:-------------:|:-----:|
|browser|(string) `chrome` or `firefox`|None|
|mobile|(boolean)|True|
|desktop|(boolean)|True|
|platform|(string) `'linux', 'windows', 'darwin', 'android', 'ios'`|None|
|custom|(string)|None|
#### Example

```python
scraper = cloudscraper.create_scraper(browser='chrome')
```

or

```python
# will give you only mobile chrome User-Agents on Android
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'android',
        'desktop': False
    }
)

# will give you only desktop firefox User-Agents on Windows
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'firefox',
        'platform': 'windows',
        'mobile': False
    }
)

# Custom will also try find the user-agent string in the browsers.json,
# If a match is found, it will use the headers and cipherSuite from that "browser",
# Otherwise a generic set of headers and cipherSuite will be used.
scraper = cloudscraper.create_scraper(
    browser={
        'custom': 'ScraperBot/1.0',
    }
)
```
------

### Debug

#### Description

Prints out header and content information of the request for debugging.

#### Parameters

Can be set as an attribute via your `cloudscraper` object or passed as an argument to `create_scraper()`, `get_tokens()`, `get_cookie_string()`.

|Parameter|Value|Default|
|-------------|:-------------:|:-----:|
|debug|(boolean)|False|

#### Example

```python
scraper = cloudscraper.create_scraper(debug=True)
```

------

### Delays

#### Description

Cloudflare IUAM challenge requires the browser to wait ~5 seconds before submitting the challenge answer, If you would like to override this delay.

#### Parameters

Can be set as an attribute via your `cloudscraper` object or passed as an argument to `create_scraper()`, `get_tokens()`, `get_cookie_string()`.

|Parameter|Value|Default|
|-------------|:-------------:|:-----:|
|delay|(float)|extracted from IUAM page|

#### Example

```python
scraper = cloudscraper.create_scraper(delay=10)
```

------

### Existing session

#### Description:

If you already have an existing Requests session, you can pass it to the function `create_scraper()` to continue using that session.

#### Parameters

|Parameter|Value|Default|
|-------------|:-------------:|:-----:|
|sess|(requests.session)|None|

#### Example

```python
session = requests.session()
scraper = cloudscraper.create_scraper(sess=session)
```

#### Note

Unfortunately, not all of Requests session attributes are easily transferable, so if you run into problems with this,

You should replace your initial session initialization call

From:
```python
sess = requests.session()
```

To:

```python
sess = cloudscraper.create_scraper()
```

------

### JavaScript Engines and Interpreters

#### Description
cloudscraper currently supports the following JavaScript Engines/Interpreters

- **[js2py](https://github.com/PiotrDabkowski/Js2Py)**
- **native**: Self made native python solver **(Default)**
- **[Node.js](https://nodejs.org/)**
- **[V8](https://github.com/sony/v8eval/)**


#### Parameters
Can be set as an attribute via your `cloudscraper` object or passed as an argument to `create_scraper()`, `get_tokens()`, `get_cookie_string()`.

|Parameter|Value|Default|
|-------------|:-------------:|:-----:|
|interpreter|(string)|`native`|

#### Example

```python
scraper = cloudscraper.create_scraper(interpreter='nodejs')
```

------
### 3rd Party Captcha Solvers

#### Note: There are currently several implementations for 3rd party Captcha solvers but they're all currently broken due to Cloudflare's rollout of hcaptcha. See [this run down](captcha_info.md) of the old implementation if you're brave of heart!

## Integration

It's easy to integrate `cloudscraper` with other applications and tools. Cloudflare uses two cookies as tokens: one to verify you made it past their challenge page and one to track your session. To bypass the challenge page, simply include both of these cookies (with the appropriate user-agent) in all HTTP requests you make.

To retrieve just the cookies (as a dictionary), use `cloudscraper.get_tokens()`. To retrieve them as a full `Cookie` HTTP header, use `cloudscraper.get_cookie_string()`.

`get_tokens` and `get_cookie_string` both accept Requests' usual keyword arguments (like `get_tokens(url, proxies={"http": "socks5://localhost:9050"})`).

Please read [Requests' documentation on request arguments](http://docs.python-requests.org/en/master/api/#requests.Session.request) for more information.

------

### User-Agent Handling

The two integration functions return a tuple of `(cookie, user_agent_string)`.

**You must use the same user-agent string for obtaining tokens and for making requests with those tokens, otherwise Cloudflare will flag you as a bot.**

That means you have to pass the returned `user_agent_string` to whatever script, tool, or service you are passing the tokens to (e.g. curl, or a specialized scraping tool), and it must use that passed user-agent when it makes HTTP requests.

------

### Integration examples

Remember, you must always use the same user-agent when retrieving or using these cookies. These functions all return a tuple of `(cookie_dict, user_agent_string)`.

------

#### Retrieving a cookie dict through a proxy

`get_tokens` is a convenience function for returning a Python dict containing Cloudflare's session cookies. For demonstration, we will configure this request to use a proxy. (Please note that if you request Cloudflare clearance tokens through a proxy, you must always use the same proxy when those tokens are passed to the server. Cloudflare requires that the challenge-solving IP and the visitor IP stay the same.)

If you do not wish to use a proxy, just don't pass the `proxies` keyword argument. These convenience functions support all of Requests' normal keyword arguments, like `params`, `data`, and `headers`.

```python
import cloudscraper

proxies = {"http": "http://localhost:8080", "https": "http://localhost:8080"}
tokens, user_agent = cloudscraper.get_tokens("http://somesite.com", proxies=proxies)
print(tokens)
# => {
    'cf_clearance': 'c8f913c707b818b47aa328d81cab57c349b1eee5-1426733163-3600',
    '__cfduid': 'dd8ec03dfdbcb8c2ea63e920f1335c1001426733158'
}
```

------

#### Retrieving a cookie string

`get_cookie_string` is a convenience function for returning the tokens as a string for use as a `Cookie` HTTP header value.

This is useful when crafting an HTTP request manually, or working with an external application or library that passes on raw cookie headers.

```python
import cloudscraper

cookie_value, user_agent = cloudscraper.get_cookie_string('http://somesite.com')

print('GET / HTTP/1.1\nCookie: {}\nUser-Agent: {}\n'.format(cookie_value, user_agent))

# GET / HTTP/1.1
# Cookie: cf_clearance=c8f913c707b818b47aa328d81cab57c349b1eee5-1426733163-3600; __cfduid=dd8ec03dfdbcb8c2ea63e920f1335c1001426733158
# User-Agent: Some/User-Agent String
```

------

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

### Cryptography

#### Description

Control communication between client and server

#### Parameters

Can be passed as an argument to `create_scraper()`.

|Parameter|Value|Default|
|-------------|:-------------:|:-----:|
|cipherSuite|(string)|None|
|ecdhCurve|(string)|prime256v1|
|server_hostname|(string)|None|

#### Example

```python
# Some servers require the use of a more complex ecdh curve than the default "prime256v1"
# It may can solve handshake failure
scraper = cloudscraper.create_scraper(ecdhCurve='secp384r1')
```

```python
# Manipulate server_hostname
scraper = cloudscraper.create_scraper(server_hostname='www.somesite.com')
scraper.get(
    'https://backend.hosting.com/',
    headers={'Host': 'www.somesite.com'}
)
```
