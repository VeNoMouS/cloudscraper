import os
import re
from setuptools import setup
from io import open

base_path = os.path.dirname(__file__)

with open(os.path.join(base_path, 'cloudscraper', '__init__.py')) as fp:
    VERSION = re.compile(r'.*__version__ = "(.*?)"',
                         re.S).match(fp.read()).group(1)

with open('README.md') as fp:
    readme = fp.read()

setup(
    name = 'cloudscraper',
    packages = ['cloudscraper'],
    long_description=readme,
    long_description_content_type='text/markdown',
    description = 'A Python module to bypass Cloudflare\'s anti-bot page. See https://github.com/venomous/cloudscraper for more information.',
    author = 'VeNoMouS',
    author_email = 'venom@gen-x.co.nz',
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
        'requests >= 2.9.2',
        'js2py >= 0.60',
        'requests_toolbelt >= 0.8.0'
    ],
    classifiers=[
      'Development Status :: 4 - Beta',
      'Intended Audience :: Developers',
      'Natural Language :: English',
      "License :: OSI Approved :: MIT License",
      "Operating System :: OS Independent",
      'Programming Language :: Python',
      'Programming Language :: Python :: 2',
      'Programming Language :: Python :: 2.7',
      'Programming Language :: Python :: 3',
      'Programming Language :: Python :: 3.4',
      'Programming Language :: Python :: 3.5',
      'Programming Language :: Python :: 3.6',
      'Programming Language :: Python :: 3.7'
    ]
)
