# cloudscraper25 - Enhanced Edition

[![PyPI version](https://badge.fury.io/py/cloudscraper25.svg)](https://badge.fury.io/py/cloudscraper25)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![image](https://img.shields.io/pypi/pyversions/cloudscraper25.svg)](https://pypi.org/project/cloudscraper25/)

**Enhanced by [Zied Boughdir](https://github.com/zinzied)**

## Latest Release: v2.5.1
- Fixed package import issues
- Improved compatibility with modern Cloudflare challenges
- Enhanced stealth mode features
- Better proxy rotation system

A Python module to bypass Cloudflare's anti-bot page (also known as "I'm Under Attack Mode", or IUAM), implemented with [Requests](https://github.com/kennethreitz/requests). This enhanced version includes support for Cloudflare v2 challenges, proxy rotation, stealth mode, and more. Cloudflare changes their techniques periodically, so I will update this repo frequently.

This can be useful if you wish to scrape or crawl a website protected with Cloudflare. Cloudflare's anti-bot page currently just checks if the client supports Javascript, though they may add additional techniques in the future.

Due to Cloudflare continually changing and hardening their protection page, cloudscraper25 requires a JavaScript Engine/interpreter to solve Javascript challenges. This allows the script to easily impersonate a regular web browser without explicitly deobfuscating and parsing Cloudflare's Javascript.

For reference, this is the default message Cloudflare uses for these sorts of pages:

```
Checking your browser before accessing website.com.

This process is automatic. Your browser will redirect to your requested content shortly.

Please allow up to 5 seconds...
```

Any script using cloudscraper25 will sleep for ~5 seconds for the first visit to any site with Cloudflare anti-bots enabled, though no delay will occur after the first request.



# Installation

Simply run `pip install cloudscraper25`. The PyPI package is at https://pypi.org/project/cloudscraper25/

```bash
pip install cloudscraper25
```

Alternatively, clone this repository and run `python setup.py install`.

## Migration from cloudscraper

If you were previously using the original `cloudscraper` package, you'll need to update your imports:

```python
# Old import
import cloudscraper  # Original package

# New import
import cloudscraper25  # Enhanced version
```

The API remains compatible, so you only need to change the import statements in your code. All function calls and parameters work the same way.

## Key Features in cloudscraper25

| Feature | Description |
|---------|-------------|
| **Modern Challenge Support** | Enhanced support for both v1 and v2 Cloudflare challenges |
| **Proxy Rotation** | Built-in smart proxy rotation with multiple strategies |
| **Stealth Mode** | Human-like behavior simulation to avoid detection |
| **Browser Emulation** | Advanced browser fingerprinting for Chrome and Firefox |
| **JavaScript Handling** | Better JS interpreter (js2py as default) for challenge solving |
| **Captcha Solvers** | Support for multiple CAPTCHA solving services |

# Dependencies

- Python 3.x
- **[Requests](https://github.com/kennethreitz/requests)** >= 2.9.2
- **[requests_toolbelt](https://pypi.org/project/requests-toolbelt/)** >= 0.9.1
- **[pyparsing](https://pypi.org/project/pyparsing/)** >= 2.4.7
- **[pyOpenSSL](https://pypi.org/project/pyOpenSSL/)** >= 22.0.0
- **[pycryptodome](https://pypi.org/project/pycryptodome/)** >= 3.15.0
- **[websocket-client](https://pypi.org/project/websocket-client/)** >= 1.3.3
- **[js2py](https://pypi.org/project/Js2Py/)** >= 0.74

`python setup.py install` will install the Python dependencies automatically. The javascript interpreters and/or engines you decide to use are the only things you need to install yourself, excluding js2py which is part of the requirements as the default.

# Javascript Interpreters and Engines

We support the following Javascript interpreters/engines.

- **[ChakraCore](https://github.com/microsoft/ChakraCore):** Library binaries can also be located [here](https://www.github.com/VeNoMouS/cloudscraper/tree/ChakraCore/).
- **[js2py](https://github.com/PiotrDabkowski/Js2Py):** >=0.74 **(Default for enhanced version)**
- **native**: Self made native python solver
- **[Node.js](https://nodejs.org/)**
- **[V8](https://github.com/sony/v8eval/):** We use Sony's [v8eval](https://v8.dev)() python module.

# Usage

The simplest way to use cloudscraper25 is by calling `create_scraper()`.

```python
import cloudscraper25

scraper = cloudscraper25.create_scraper()  # returns a CloudScraper instance
# Or: scraper = cloudscraper25.CloudScraper()  # CloudScraper inherits from requests.Session
print(scraper.get("http://somesite.com").text)  # => "<!DOCTYPE html><html><head>..."
```

That's it...

Any requests made from this session object to websites protected by Cloudflare anti-bot will be handled automatically. Websites not using Cloudflare will be treated normally. You don't need to configure or call anything further, and you can effectively treat all websites as if they're not protected with anything.

You use cloudscraper25 exactly the same way you use Requests. `cloudScraper` works identically to a Requests `Session` object, just instead of calling `requests.get()` or `requests.post()`, you call `scraper.get()` or `scraper.post()`.

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
scraper = cloudscraper25.create_scraper(disableCloudflareV1=True)
```

------

### Disable Cloudflare V2
#### Description

If you don't want to even attempt Cloudflare v2 solving..

#### Parameters


|Parameter|Value|Default|
|-------------|:-------------:|:-----:|
|disableCloudflareV2|(boolean)|False|

#### Example

```python
scraper = cloudscraper25.create_scraper(disableCloudflareV2=True)
```

------

### Proxy Rotation
#### Description

Automatically rotate through a list of proxies to avoid IP-based blocking.

#### Parameters

|Parameter|Value|Default|
|-------------|:-------------:|:-----:|
|rotating_proxies|(list or dict)|None|
|proxy_options|(dict)|{}|

#### `proxy_options` Parameters

|Parameter|Value|Default|
|-------------|:-------------:|:-----:|
|rotation_strategy|(string) `sequential`, `random`, or `smart`|`sequential`|
|ban_time|(int) seconds to ban a proxy after failure|300|

#### Example

```python
proxies = [
    'http://user:pass@proxy1.example.com:8080',
    'http://user:pass@proxy2.example.com:8080',
    'http://user:pass@proxy3.example.com:8080'
]

scraper = cloudscraper25.create_scraper(
    rotating_proxies=proxies,
    proxy_options={
        'rotation_strategy': 'smart',
        'ban_time': 300
    }
)
```

------

### Stealth Mode
#### Description

Enable stealth techniques to better mimic human behavior and avoid detection.

#### Parameters

|Parameter|Value|Default|
|-------------|:-------------:|:-----:|
|enable_stealth|(boolean)|True|
|stealth_options|(dict)|{}|

#### `stealth_options` Parameters

|Parameter|Value|Default|
|-------------|:-------------:|:-----:|
|min_delay|(float) minimum delay between requests|1.0|
|max_delay|(float) maximum delay between requests|5.0|
|human_like_delays|(boolean) add random delays between requests|True|
|randomize_headers|(boolean) randomize headers to avoid fingerprinting|True|
|browser_quirks|(boolean) apply browser-specific quirks|True|

#### Example

```python
scraper = cloudscraper25.create_scraper(
    enable_stealth=True,
    stealth_options={
        'min_delay': 2.0,
        'max_delay': 6.0,
        'human_like_delays': True,
        'randomize_headers': True,
        'browser_quirks': True
    }
)
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
scraper = cloudscraper25.create_scraper(allow_brotli=False)
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
scraper = cloudscraper25.create_scraper(browser='chrome')
```

or

```python
# will give you only mobile chrome User-Agents on Android
scraper = cloudscraper25.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'android',
        'desktop': False
    }
)

# will give you only desktop firefox User-Agents on Windows
scraper = cloudscraper25.create_scraper(
    browser={
        'browser': 'firefox',
        'platform': 'windows',
        'mobile': False
    }
)

# Custom will also try find the user-agent string in the browsers.json,
# If a match is found, it will use the headers and cipherSuite from that "browser",
# Otherwise a generic set of headers and cipherSuite will be used.
scraper = cloudscraper25.create_scraper(
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

Can be set as an attribute via your `cloudscraper25` object or passed as an argument to `create_scraper()`, `get_tokens()`, `get_cookie_string()`.

|Parameter|Value|Default|
|-------------|:-------------:|:-----:|
|debug|(boolean)|False|

#### Example

```python
scraper = cloudscraper25.create_scraper(debug=True)
```

------

### Delays

#### Description

Cloudflare IUAM challenge requires the browser to wait ~5 seconds before submitting the challenge answer, If you would like to override this delay.

#### Parameters

Can be set as an attribute via your `cloudscraper25` object or passed as an argument to `create_scraper()`, `get_tokens()`, `get_cookie_string()`.

|Parameter|Value|Default|
|-------------|:-------------:|:-----:|
|delay|(float)|extracted from IUAM page|

#### Example

```python
scraper = cloudscraper25.create_scraper(delay=10)
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
scraper = cloudscraper25.create_scraper(sess=session)
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
sess = cloudscraper25.create_scraper()
```

------

### JavaScript Engines and Interpreters

#### Description
cloudscraper25 currently supports the following JavaScript Engines/Interpreters

- **[ChakraCore](https://github.com/microsoft/ChakraCore)**
- **[js2py](https://github.com/PiotrDabkowski/Js2Py)** **(Default in enhanced version)**
- **native**: Self made native python solver
- **[Node.js](https://nodejs.org/)**
- **[V8](https://github.com/sony/v8eval/)**


#### Parameters
Can be set as an attribute via your `cloudscraper25` object or passed as an argument to `create_scraper()`, `get_tokens()`, `get_cookie_string()`.

|Parameter|Value|Default|
|-------------|:-------------:|:-----:|
|interpreter|(string)|`js2py`|

#### Example

```python
scraper = cloudscraper25.create_scraper(interpreter='nodejs')
```

#### Note

The enhanced version uses `js2py` as the default interpreter because it provides better compatibility with modern Cloudflare challenges. If you encounter issues, you can try other interpreters.

------

### 3rd Party Captcha Solvers

#### Description
`cloudscraper25` currently supports the following 3rd party Captcha solvers, should you require them.

- **[2captcha](https://www.2captcha.com/)**
- **[anticaptcha](https://www.anti-captcha.com/)**
- **[CapSolver](https://capsolver.com/)**
- **[CapMonster Cloud](https://capmonster.cloud/)**
- **[deathbycaptcha](https://www.deathbycaptcha.com/)**
- **[9kw](https://www.9kw.eu/)**
- **__return_response__**

#### Note

I am working on adding more 3rd party solvers, if you wish to have a service added that is not currently supported, please raise a support ticket on github.

##### Required Parameters

Can be set as an attribute via your `cloudscraper25` object or passed as an argument to `create_scraper()`, `get_tokens()`, `get_cookie_string()`.

|Parameter|Value|Default|
|-------------|:-------------:|:-----:|
|captcha|(dict)|None|

------

#### 2captcha

##### Required `captcha` Parameters

|Parameter|Value|Required|Default|
|-------------|:-------------:|:-----:|:-----:|
|provider|(string) `2captcha`| yes||
|api_key|(string)| yes||
|no_proxy|(boolean)|no|False|

##### Note

if proxies are set you can disable sending the proxies to 2captcha by setting `no_proxy` to `True`

##### Example

```python
scraper = cloudscraper25.create_scraper(
  captcha={
    'provider': '2captcha',
    'api_key': 'your_2captcha_api_key'
  }
)
```

------

#### anticaptcha

##### Required `captcha` Parameters

|Parameter|Value|Required|Default|
|-------------|:-------------:|:-----:|:-----:|
|provider|(string) `anticaptcha`|yes||
|api_key|(string)|yes||
|no_proxy|(boolean)|no|False|

##### Note

if proxies are set you can disable sending the proxies to anticaptcha by setting `no_proxy` to `True`

##### Example

```python
scraper = cloudscraper25.create_scraper(
  captcha={
    'provider': 'anticaptcha',
    'api_key': 'your_anticaptcha_api_key'
  }
)
```

------

#### CapSolver

##### Required `captcha` Parameters

|Parameter|Value|Required|Default|
|-------------|:-------------:|:-----:|:-----:|
|provider|(string) `captchaai`|yes||
|api_key|(string)|yes||


##### Example

```python
scraper = cloudscraper25.create_scraper(
  captcha={
    'provider': 'capsolver',
    'api_key': 'your_captchaai_api_key'
  }
)
```

------

#### CapMonster Cloud

##### Required `captcha` Parameters

|Parameter|Value|Required|Default|
|-------------|:-------------:|:-----:|:-----:|
|provider|(string) `capmonster`| yes||
|clientKey|(string)| yes||
|no_proxy|(boolean)|no|False|

##### Note

if proxies are set you can disable sending the proxies to CapMonster by setting `no_proxy` to `True`

##### Example

```python
scraper = cloudscraper25.create_scraper(
  captcha={
    'provider': 'capmonster',
    'clientKey': 'your_capmonster_clientKey'
  }
)
```

------

#### deathbycaptcha

##### Required `captcha` Parameters

|Parameter|Value|Required|Default|
|-------------|:-------------:|:-----:|:-----:|
|provider|(string) `deathbycaptcha`|yes||
|username|(string)|yes||
|password|(string)|yes||

##### Example

```python
scraper = cloudscraper25.create_scraper(
  captcha={
    'provider': 'deathbycaptcha',
    'username': 'your_deathbycaptcha_username',
    'password': 'your_deathbycaptcha_password',
  }
)
```

------

#### 9kw

##### Required `captcha` Parameters

|Parameter|Value|Required|Default|
|-------------|:-------------:|:-----:|:-----:|
|provider|(string) `9kw`|yes||
|api_key|(string)|yes||
|maxtimeout|(int)|no|180|

##### Example

```python
scraper = cloudscraper25.create_scraper(
  captcha={
    'provider': '9kw',
    'api_key': 'your_9kw_api_key',
    'maxtimeout': 300
  }
)
```

------

#### return_response

Use this if you want the requests response payload without solving the Captcha.

##### Required `captcha` Parameters

|Parameter|Value|Required|Default|
|-------------|:-------------:|:-----:|:-----:|
|provider|(string) `return_response`| yes||

##### Example
```python
scraper = cloudscraper25.create_scraper(
  captcha={'provider': 'return_response'}
)
```

## Integration

It's easy to integrate `cloudscraper25` with other applications and tools. Cloudflare uses two cookies as tokens: one to verify you made it past their challenge page and one to track your session. To bypass the challenge page, simply include both of these cookies (with the appropriate user-agent) in all HTTP requests you make.

To retrieve just the cookies (as a dictionary), use `cloudscraper25.get_tokens()`. To retrieve them as a full `Cookie` HTTP header, use `cloudscraper25.get_cookie_string()`.

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
import cloudscraper25

# Using a single proxy
proxies = {"http": "http://localhost:8080", "https": "http://localhost:8080"}
tokens, user_agent = cloudscraper25.get_tokens("http://somesite.com", proxies=proxies)
print(tokens)
# => {
    'cf_clearance': 'c8f913c707b818b47aa328d81cab57c349b1eee5-1426733163-3600',
    '__cfduid': 'dd8ec03dfdbcb8c2ea63e920f1335c1001426733158',
    'cf_chl_2': 'some_value',
    'cf_chl_prog': 'some_value'
}

# Using proxy rotation
rotating_proxies = [
    'http://user:pass@proxy1.example.com:8080',
    'http://user:pass@proxy2.example.com:8080',
    'http://user:pass@proxy3.example.com:8080'
]

tokens, user_agent = cloudscraper25.get_tokens(
    "http://somesite.com",
    rotating_proxies=rotating_proxies,
    proxy_options={
        'rotation_strategy': 'smart',
        'ban_time': 300
    },
    enable_stealth=True,
    stealth_options={
        'min_delay': 2.0,
        'max_delay': 6.0
    }
)
```

------

#### Retrieving a cookie string

`get_cookie_string` is a convenience function for returning the tokens as a string for use as a `Cookie` HTTP header value.

This is useful when crafting an HTTP request manually, or working with an external application or library that passes on raw cookie headers.

```python
import cloudscraper25

cookie_value, user_agent = cloudscraper25.get_cookie_string('http://somesite.com')

print('GET / HTTP/1.1\nCookie: {}\nUser-Agent: {}\n'.format(cookie_value, user_agent))

# GET / HTTP/1.1
# Cookie: cf_clearance=c8f913c707b818b47aa328d81cab57c349b1eee5-1426733163-3600; __cfduid=dd8ec03dfdbcb8c2ea63e920f1335c1001426733158
# User-Agent: Some/User-Agent String
```

------

#### curl example

Here is an example of integrating cloudscraper25 with curl. As you can see, all you have to do is pass the cookies and user-agent to curl.

```python
import subprocess
import cloudscraper25

# With get_tokens() cookie dict:

# tokens, user_agent = cloudscraper25.get_tokens("http://somesite.com")
# cookie_arg = 'cf_clearance={}; __cfduid={}'.format(tokens['cf_clearance'], tokens['__cfduid'])

# With get_cookie_string() cookie header; recommended for curl and similar external applications:

cookie_arg, user_agent = cloudscraper25.get_cookie_string('http://somesite.com')

# With a custom user-agent string you can optionally provide:

# ua = "Scraping Bot"
# cookie_arg, user_agent = cloudscraper25.get_cookie_string("http://somesite.com", user_agent=ua)

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
cookie_arg, user_agent = cloudscraper25.get_cookie_string(url)
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
scraper = cloudscraper25.create_scraper(ecdhCurve='secp384r1')
```

```python
# Manipulate server_hostname
scraper = cloudscraper25.create_scraper(server_hostname='www.somesite.com')
scraper.get(
    'https://backend.hosting.com/',
    headers={'Host': 'www.somesite.com'}
)
```

# Enhanced Features

This enhanced version of cloudscraper provides better capabilities for bypassing modern Cloudflare protection mechanisms:

1. **Cloudflare v2 Challenge Support** - Better handling of modern challenges
2. **Proxy Rotation** - Smart rotation with multiple strategies
3. **Stealth Mode** - Human-like behavior simulation
4. **Improved JavaScript Handling** - Better JS interpreter (js2py as default)
5. **Enhanced Cookie Management** - Support for newer Cloudflare cookie types

## Example Using All Enhanced Features

```python
import cloudscraper25

# Create a scraper with all enhanced features
scraper = cloudscraper25.create_scraper(
    # Use js2py interpreter for better compatibility
    interpreter='js2py',

    # Enable proxy rotation
    rotating_proxies=[
        'http://user:pass@proxy1.example.com:8080',
        'http://user:pass@proxy2.example.com:8080',
        'http://user:pass@proxy3.example.com:8080'
    ],
    proxy_options={
        'rotation_strategy': 'smart',
        'ban_time': 300
    },

    # Enable stealth mode
    enable_stealth=True,
    stealth_options={
        'min_delay': 2.0,
        'max_delay': 6.0,
        'human_like_delays': True,
        'randomize_headers': True,
        'browser_quirks': True
    },

    # Set browser fingerprint
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'mobile': False
    },

    # Enable debugging if needed
    debug=False
)

# Make a request to a Cloudflare-protected site
response = scraper.get('https://example.com')
print(response.text)
```

## Credits

- Original cloudscraper by [VeNoMouS](https://github.com/VeNoMouS/cloudscraper)
- Enhanced Edition by [Zied Boughdir](https://github.com/zinzied)

## Testing

Quick test to verify the library is working:

```python
import cloudscraper25

# Create a scraper instance
scraper = cloudscraper25.create_scraper(browser='chrome')

# Make a request to a Cloudflare-protected site
response = scraper.get('https://example.com')
print(f"Status code: {response.status_code}")
```

### Troubleshooting Tips

If you encounter issues:

1. **Try different browser emulation** - Some sites work better with Chrome vs Firefox
2. **Enable stealth mode** - Helps bypass sophisticated protection
3. **Use proxy rotation** - For IP blocks or rate limits
4. **Try different JS interpreters** - js2py, nodejs, or v8

## Support

For issues or questions, please open an issue on the GitHub repository.

```bash
pip install --upgrade cloudscraper25  # Always use the latest version
```
