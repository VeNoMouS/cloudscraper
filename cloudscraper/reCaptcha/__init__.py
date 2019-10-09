import sys
import logging
import abc

if sys.version_info >= (3, 4):
    ABC = abc.ABC  # noqa
else:
    ABC = abc.ABCMeta('ABC', (), {})

# ------------------------------------------------------------------------------- #

captchaSolvers = {}

# ------------------------------------------------------------------------------- #


class reCaptcha(ABC):
    @abc.abstractmethod
    def __init__(self, name):
        captchaSolvers[name] = self

    # ------------------------------------------------------------------------------- #

    @classmethod
    def dynamicImport(cls, name):
        if name not in captchaSolvers:
            try:
                __import__('{}.{}'.format(cls.__module__, name))
                if not isinstance(captchaSolvers.get(name), reCaptcha):
                    raise ImportError('The anti reCaptcha provider was not initialized.')
            except ImportError:
                logging.error("Unable to load {} anti reCaptcha provider".format(name))
                raise

        return captchaSolvers[name]

    # ------------------------------------------------------------------------------- #

    @abc.abstractmethod
    def getCaptchaAnswer(self, site_url, site_key, reCaptchaParams):
        pass

    # ------------------------------------------------------------------------------- #

    def solveCaptcha(self, site_url, site_key, reCaptchaParams):
        return self.getCaptchaAnswer(site_url, site_key, reCaptchaParams)
