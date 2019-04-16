import os
import re
from setuptools import setup

base_path = os.path.dirname(__file__)

with open(os.path.join(base_path, 'cloudscraper', '__init__.py')) as fp:
    VERSION = re.compile(r'.*__version__ = "(.*?)"', re.S).match(fp.read()).group(1)

setup(
    name = 'cloudscraper',
    packages = ['cloudscraper'],
    version = VERSION,
    description = 'A Python module to bypass Cloudflare\'s anti-bot page. See https://github.com/venomous/cloudscraper for more information.',
    author = 'VeNoMouS',
    author_email = 'venom@gen-x.co.nz',
    url = 'https://github.com/venomous/cloudscraper',
    keywords = [
        'cloudflare',
        'scraping'
    ],
    include_package_data = True,
    install_requires = [
        'requests >= 2.9.2',
        'js2py >= 0.60',
        'requests_toolbelt >= 0.8.0'
    ]
)