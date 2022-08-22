import os
import re
from setuptools import setup, find_packages
from io import open

with open(os.path.join(os.path.dirname(__file__), "cloudscraper", "__init__.py")) as fp:
    VERSION = re.match(r".*__version__ = \"(.*?)\"", fp.read(), re.S).group(1)

with open("README.md", "r", encoding="utf-8") as fp:
    readme = fp.read()

setup(
    name="cloudscraper",
    author="curseforge-mirror",
    version=VERSION,
    packages=find_packages(exclude=["tests*"]),
    description="A Python module to bypass Cloudflare's anti-bot page.",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/curseforge-mirror/cloudscraper",
    keywords=[
        "cloudflare",
        "scraping",
        "ddos",
        "scrape",
        "webscraper",
        "anti-bot",
        "waf",
        "iuam",
        "bypass",
        "challenge",
    ],
    include_package_data=True,
    install_requires=[
        "requests",
        "requests_toolbelt",
        "pyparsing",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
