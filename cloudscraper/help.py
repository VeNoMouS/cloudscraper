import json
import platform
import requests
import ssl
import sys
import urllib3

from collections import OrderedDict
from . import __version__ as cloudscraper_version

# ------------------------------------------------------------------------------- #


def getPossibleCiphers():
    try:
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.set_ciphers('ALL')
        return sorted([cipher['name'] for cipher in context.get_ciphers()])
    except AttributeError:
        return 'get_ciphers() is unsupported'

# ------------------------------------------------------------------------------- #


def _pythonVersion():
    interpreter = platform.python_implementation()
    interpreter_version = platform.python_version()

    if interpreter == 'PyPy':
        interpreter_version = '{}.{}.{}'.format(
            sys.pypy_version_info.major,
            sys.pypy_version_info.minor,
            sys.pypy_version_info.micro
        )
        if sys.pypy_version_info.releaselevel != 'final':
            interpreter_version = '{}{}'.format(
                interpreter_version,
                sys.pypy_version_info.releaselevel
            )

    return {
        'name': interpreter,
        'version': interpreter_version
    }

# ------------------------------------------------------------------------------- #


def systemInfo():
    try:
        platform_info = {
            'system': platform.system(),
            'release': platform.release(),
        }
    except IOError:
        platform_info = {
            'system': 'Unknown',
            'release': 'Unknown',
        }

    return OrderedDict([
        ('platform', platform_info),
        ('interpreter', _pythonVersion()),
        ('cloudscraper', cloudscraper_version),
        ('requests', requests.__version__),
        ('urllib3', urllib3.__version__),
        ('OpenSSL', OrderedDict(
            [
                ('version', ssl.OPENSSL_VERSION),
                ('ciphers', getPossibleCiphers())
            ]
        ))
    ])

# ------------------------------------------------------------------------------- #


if __name__ == '__main__':
    print(json.dumps(systemInfo(), indent=4))
