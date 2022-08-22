### Captcha Info (for the brave of heart)
#### Description
`cloudscraper` currently supports the following 3rd party Captcha solvers, should you require them.

- **[2captcha](https://www.2captcha.com/)**
- **[anticaptcha](https://www.anti-captcha.com/)**
- **[CapMonster Cloud](https://capmonster.cloud/)**
- **[deathbycaptcha](https://www.deathbycaptcha.com/)**
- **[9kw](https://www.9kw.eu/)**
- **__return_response__**

#### Note

I am working on adding more 3rd party solvers, if you wish to have a service added that is not currently supported, please raise a support ticket on github.

##### Required Parameters

Can be set as an attribute via your `cloudscraper` object or passed as an argument to `create_scraper()`, `get_tokens()`, `get_cookie_string()`.

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
scraper = cloudscraper.create_scraper(
  interpreter='nodejs',
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
scraper = cloudscraper.create_scraper(
  interpreter='nodejs',
  captcha={
    'provider': 'anticaptcha',
    'api_key': 'your_anticaptcha_api_key'
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
scraper = cloudscraper.create_scraper(
  interpreter='nodejs',
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
scraper = cloudscraper.create_scraper(
  interpreter='nodejs',
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
scraper = cloudscraper.create_scraper(
  interpreter='nodejs',
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
scraper = cloudscraper.create_scraper(
  interpreter='nodejs',
  captcha={'provider': 'return_response'}
)
```