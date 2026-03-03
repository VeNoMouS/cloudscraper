# cloudscraper

<p align="center">
  <a href="https://pypi.org/project/cloudscraper/">
    <img src="https://img.shields.io/pypi/v/cloudscraper.svg" alt="PyPI Version">
  </a>
  <a href="https://pypi.org/project/cloudscraper/">
    <img src="https://img.shields.io/pypi/pyversions/cloudscraper.svg" alt="Python Versions">
  </a>
  <a href="https://opensource.org/licenses/MIT">
    <img src="https://img.shields.io/pypi/l/cloudscraper.svg" alt="License">
  </a>
  <a href="https://github.com/venomous/cloudscraper/actions">
    <img src="https://github.com/venomous/cloudscraper/workflows/CI/badge.svg" alt="CI Status">
  </a>
</p>

A powerful Python library to bypass Cloudflare's anti-bot protection, including support for:
- **Cloudflare v1** (IUAM - I'm Under Attack Mode)
- **Cloudflare v2** (JavaScript challenges)
- **Cloudflare v3** (JavaScript VM challenges)
- **Cloudflare Turnstile** (CAPTCHA alternative)
- **Proxy rotation**
- **Stealth mode** (human-like behavior)

## Installation

```bash
pip install cloudscraper
```

Or install the latest development version:

```bash
pip install git+https://github.com/venomous/cloudscraper.git
```

## Quick Start

```python
import cloudscraper

# Create a scraper (automatically handles Cloudflare challenges)
scraper = cloudscraper.create_scraper()

# Make requests just like with requests library
response = scraper.get("https://example.com")
print(response.text)
```

That's it! The library automatically detects and solves Cloudflare challenges.

## Features

### All Challenge Types Supported

| Challenge Type | Support | Description |
|----------------|---------|-------------|
| Cloudflare v1 | ✅ | Classic IUAM JavaScript challenges |
| Cloudflare v2 | ✅ | Modern JavaScript challenges |
| Cloudflare v3 | ✅ | JavaScript VM-based challenges |
| Turnstile | ✅ | Cloudflare's CAPTCHA alternative |
| reCAPTCHA | ✅ | Via external providers |
| hCaptcha | ✅ | Via external providers |

### Advanced Protection Bypass

- **Stealth Mode**: Mimics real browser behavior
- **Proxy Rotation**: Automatic proxy cycling
- **Session Management**: Automatic session refresh
- **TLS Fingerprint**: Customizable cipher suites
- **User-Agent Rotation**: Random UA selection

### Highly Configurable

```python
import cloudscraper

# Full configuration example
scraper = cloudscraper.create_scraper(
    # Browser emulation
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True,
        'mobile': False
    },
    
    # Challenge handling
    interpreter='js2py',  # js2py, nodejs, native, v8
    delay=5.0,            # Challenge solve delay
    
    # Stealth mode
    enable_stealth=True,
    stealth_options={
        'min_delay': 2.0,
        'max_delay': 6.0,
        'human_like_delays': True,
        'randomize_headers': True,
        'browser_quirks': True
    },
    
    # Proxy rotation
    rotating_proxies=[
        'http://user:pass@proxy1:8080',
        'http://user:pass@proxy2:8080',
    ],
    proxy_options={
        'rotation_strategy': 'smart',  # sequential, random, smart
        'ban_time': 300               # seconds to ban failed proxy
    },
    
    # Session management
    session_refresh_interval=3600,  # seconds
    auto_refresh_on_403=True,
    max_403_retries=3,
    
    # Request throttling
    min_request_interval=1.0,    # seconds between requests
    max_concurrent_requests=1,
    rotate_tls_ciphers=True,
    
    # CAPTCHA solving
    captcha={
        'provider': '2captcha',      # 2captcha, anticaptcha, etc.
        'api_key': 'YOUR_API_KEY'
    },
    
    # Debug
    debug=True
)
```

## Usage Examples

### Basic Request

```python
import cloudscraper

scraper = cloudscraper.create_scraper()
response = scraper.get("https://cloudflare-protected-site.com")
print(response.status_code)
```

### Get Cloudflare Tokens

```python
import cloudscraper

# Get tokens for use with other HTTP clients
tokens, user_agent = cloudscraper.get_tokens("https://example.com")
# Returns: ({'cf_clearance': '...', '__cfduid': '...'}, 'Mozilla/5.0 ...')

# Use with requests
import requests
session = requests.Session()
session.headers['User-Agent'] = user_agent
session.cookies.update(tokens)
response = session.get("https://example.com")
```

### Get Cookie String

```python
import cloudscraper

# Get cookies as a string for curl/other tools
cookie_string, user_agent = cloudscraper.get_cookie_string("https://example.com")
# Returns: ('cf_clearance=...; __cfduid=...', 'Mozilla/5.0 ...')

# Use with curl
# curl -b "$cookie_string" -A "$user_agent" https://example.com
```

### Session Reuse

```python
import cloudscraper
import pickle

# Save session
scraper = cloudscraper.create_scraper()
# ... make requests ...

# Save to file
with open('session.pkl', 'wb') as f:
    pickle.dump(scraper, f)

# Load session later
with open('session.pkl', 'rb') as f:
    scraper = pickle.load(f)
```

## API Reference

### cloudscraper.create_scraper(sess=None, **kwargs)

Create a CloudScraper instance.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sess` | Session | None | Existing requests Session to copy |
| `browser` | str/dict | None | Browser configuration |
| `debug` | bool | False | Enable debug output |
| `delay` | float | auto | Challenge delay in seconds |
| `interpreter` | str | 'js2py' | JS interpreter (js2py, nodejs, native, v8) |
| `captcha` | dict | {} | CAPTCHA provider config |
| `enable_stealth` | bool | True | Enable stealth mode |
| `stealth_options` | dict | {} | Stealth configuration |
| `rotating_proxies` | list | None | List of proxy URLs |
| `proxy_options` | dict | {} | Proxy configuration |
| `session_refresh_interval` | int | 3600 | Session refresh interval |
| `auto_refresh_on_403` | bool | True | Auto refresh on 403 |
| `max_403_retries` | int | 3 | Max 403 retries |
| `min_request_interval` | float | 1.0 | Min seconds between requests |
| `max_concurrent_requests` | int | 1 | Max concurrent requests |
| `rotate_tls_ciphers` | bool | True | Rotate TLS ciphers |
| `disableCloudflareV1` | bool | False | Disable v1 challenges |
| `disableCloudflareV2` | bool | False | Disable v2 challenges |
| `disableCloudflareV3` | bool | False | Disable v3 challenges |
| `disableTurnstile` | bool | False | Disable Turnstile |

**Returns:** CloudScraper instance

### cloudscraper.get_tokens(url, **kwargs)

Get Cloudflare tokens for a URL.

**Parameters:**
- `url` (str): Target URL
- `**kwargs`: Same as create_scraper()

**Returns:** tuple of (cookies_dict, user_agent_string)

### cloudscraper.get_cookie_string(url, **kwargs)

Get Cloudflare cookies as a Cookie header string.

**Parameters:**
- `url` (str): Target URL
- `**kwargs`: Same as create_scraper()

**Returns:** tuple of (cookie_string, user_agent_string)

### CloudScraper Class

Inherits from requests.Session, so all standard request methods work:

```python
scraper.get(url, params=None, **kwargs)
scraper.post(url, data=None, json=None, **kwargs)
scraper.put(url, data=None, **kwargs)
scraper.delete(url, **kwargs)
scraper.head(url, **kwargs)
scraper.options(url, **kwargs)
```

## CAPTCHA Providers

Supported CAPTCHA providers:

| Provider | Config Key | Required Parameters |
|----------|------------|---------------------|
| 2captcha | provider: '2captcha' | api_key |
| Anti-Captcha | provider: 'anticaptcha' | api_key |
| CapSolver | provider: 'capsolver' | api_key |
| CapMonster | provider: 'capmonster' | clientKey |
| DeathByCaptcha | provider: 'deathbycaptcha' | username, password |
| 9kw | provider: '9kw' | api_key |

Example with 2captcha:

```python
import cloudscraper

scraper = cloudscraper.create_scraper(
    captcha={
        'provider': '2captcha',
        'api_key': 'YOUR_2CAPTCHA_API_KEY'
    }
)

# Turnstile/hCaptcha will be automatically solved
response = scraper.get("https://turnstile-site.com")
```

## JavaScript Interpreters

| Interpreter | Description |
|-------------|-------------|
| js2py | Pure Python JS engine (default) |
| nodejs | Node.js interpreter |
| native | Built-in Python solver |
| v8 | Sony's v8eval |

## Configuration Examples

### Chrome Browser Emulation

```python
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True,
        'mobile': False
    }
)
```

### Firefox Mobile Emulation

```python
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'firefox',
        'platform': 'android',
        'mobile': True,
        'desktop': False
    }
)
```

### Proxy Rotation with Smart Strategy

```python
scraper = cloudscraper.create_scraper(
    rotating_proxies=[
        'http://user:pass@proxy1:8080',
        'http://user:pass@proxy2:8080',
        'http://user:pass@proxy3:8080',
    ],
    proxy_options={
        'rotation_strategy': 'smart',  # Tracks success rates
        'ban_time': 300  # Ban failed proxies for 5 minutes
    }
)
```

### Session Persistence

```python
import cloudscraper
import pickle

# Create and use scraper
scraper = cloudscraper.create_scraper()
response = scraper.get("https://example.com")

# Save session
with open('session.pkl', 'wb') as f:
    pickle.dump(scraper, f)

# Load session later
with open('session.pkl', 'rb') as f:
    scraper = pickle.load(f)

# Continue using
response = scraper.get("https://example.com")
```

## Error Handling

```python
import cloudscraper
from cloudscraper.exceptions import (
    CloudflareLoopProtection,
    CloudflareIUAMError,
    CloudflareChallengeError,
    CloudflareCode1020,
    CloudflareCaptchaProvider
)

try:
    scraper = cloudscraper.create_scraper()
    response = scraper.get("https://cloudflare-protected-site.com")
except CloudflareLoopProtection:
    print("Too many challenge attempts - try a new session")
except CloudflareCode1020:
    print("IP blocked by Cloudflare")
except CloudflareCaptchaProvider:
    print("CAPTCHA solving required - configure provider")
except Exception as e:
    print(f"Other error: {e}")
```

## Performance Tips

1. **Reuse Sessions**: Create one CloudScraper instance and reuse it
2. **Disable Unused Challenges**: If you only need v3, disable others:
   ```python
   scraper = cloudscraper.create_scraper(
       disableCloudflareV1=True,
       disableCloudflareV2=True,
       disableTurnstile=True
   )
   ```
3. **Use Smart Proxy Rotation**: Reduces detection and blocks
4. **Adjust Request Interval**: Increase min_request_interval if getting rate-limited

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_modern.py

# Run with coverage
pytest --cov=cloudscraper --cov-report=html

# Skip slow integration tests
pytest -m "not slow"
```

## Requirements

- Python 3.8+
- requests >= 2.31.0
- requests-toolbelt >= 1.0.0
- pyparsing >= 3.1.0
- pyOpenSSL >= 24.0.0
- pycryptodome >= 3.20.0
- websocket-client >= 1.7.0
- js2py >= 0.74
- brotli >= 1.1.0
- certifi >= 2024.2.2

## Architecture

```
cloudscraper/
├── __init__.py          # Main CloudScraper class
├── base.py              # Abstract base for challenge handlers
├── cloudflare.py        # v1 challenge handler
├── cloudflare_v2.py     # v2 challenge handler
├── cloudflare_v3.py     # v3 challenge handler
├── turnstile.py         # Turnstile handler
├── session_manager.py   # Session health management
├── request_throttler.py # Rate limiting
├── proxy_manager.py     # Proxy rotation
├── stealth.py           # Stealth mode
├── constants.py         # Constants
├── exceptions.py        # Custom exceptions
├── user_agent/          # User agent handling
│   └── browsers.json
├── interpreters/         # JS interpreters
└── captcha/            # CAPTCHA providers
```

## License

MIT License - see LICENSE for details.

## Credits

- Original cloudscraper by VeNoMouS
- Enhanced Edition by Zied Boughdir
- Contributors

## Disclaimer

This library is intended for educational and legitimate web scraping purposes only. Always respect the target website's terms of service and robots.txt. Do not use this library for malicious purposes.
