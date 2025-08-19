import os
import re
from setuptools import setup
from io import open

with open(os.path.join(os.path.dirname(__file__), 'cloudscraper', '__init__.py'), encoding="utf-8") as fp:
    VERSION = re.match(r'.*__version__ = \'(.*?)\'', fp.read(), re.S).group(1)

with open('README.md', 'r', encoding='utf-8') as fp:
    readme = fp.read()

setup(
    name = 'cloudscraper',
    author = 'VeNoMouS, Zied Boughdir',
    author_email = 'venom@cloudscraper.io',
    version=VERSION,
    packages = ['cloudscraper', 'cloudscraper.captcha', 'cloudscraper.interpreters', 'cloudscraper.user_agent'],
    py_modules = [],
    python_requires='>=3.8',
    description = 'Enhanced Python module to bypass Cloudflare\'s anti-bot page with support for v2 challenges, proxy rotation, and stealth mode.',
    long_description=readme,
    long_description_content_type='text/markdown',
    url = 'https://github.com/venomous/cloudscraper',
    keywords = [
        'cloudflare',
        'scraping',
        'ddos',
        'scrape',
        'webscraper',
        'anti-bot',
        'waf',
        'iuam',
        'bypass',
        'challenge'
    ],
    include_package_data = True,
    install_requires = [
        'requests >= 2.31.0',
        'requests_toolbelt >= 1.0.0',
        'pyparsing >= 3.1.0',
        'pyOpenSSL >= 24.0.0',
        'pycryptodome >= 3.20.0',
        'websocket-client >= 1.7.0',
        'js2py >= 0.74',
        'brotli >= 1.1.0',
        'certifi >= 2024.2.2'
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
