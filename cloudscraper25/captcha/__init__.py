import abc
import logging
import sys

if sys.version_info >= (3, 4):
    ABC = abc.ABC  # noqa
else:
    ABC = abc.ABCMeta('ABC', (), {})

# ------------------------------------------------------------------------------- #

captchaSolvers = {}

# ------------------------------------------------------------------------------- #


class Captcha(ABC):
    @abc.abstractmethod
    def __init__(self, name):
        captchaSolvers[name] = self

    # ------------------------------------------------------------------------------- #

    @classmethod
    def dynamicImport(cls, name):
        if name not in captchaSolvers:
            try:
                __import__(f'{cls.__module__}.{name}')
                if not isinstance(captchaSolvers.get(name), Captcha):
                    raise ImportError('The anti captcha provider was not initialized.')
            except ImportError as e:
                sys.tracebacklimit = 0
                logging.error(f'Unable to load {name} anti captcha provider -> {e}')
                raise

        return captchaSolvers[name]

    # ------------------------------------------------------------------------------- #

    @abc.abstractmethod
    def getCaptchaAnswer(self, captchaType, url, siteKey, captchaParams):
        pass

    # ------------------------------------------------------------------------------- #

    def solveCaptcha(self, captchaType, url, siteKey, captchaParams):
        return self.getCaptchaAnswer(captchaType, url, siteKey, captchaParams)
