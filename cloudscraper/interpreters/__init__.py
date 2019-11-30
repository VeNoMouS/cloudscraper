import sys
import logging
import abc

if sys.version_info >= (3, 4):
    ABC = abc.ABC  # noqa
else:
    ABC = abc.ABCMeta('ABC', (), {})

# ------------------------------------------------------------------------------- #

interpreters = {}
BUG_REPORT = 'Cloudflare may have changed their technique, or there may be a bug in the script.'

# ------------------------------------------------------------------------------- #


class JavaScriptInterpreter(ABC):

    # ------------------------------------------------------------------------------- #

    @abc.abstractmethod
    def __init__(self, name):
        interpreters[name] = self

    # ------------------------------------------------------------------------------- #

    @classmethod
    def dynamicImport(cls, name):
        if name not in interpreters:
            try:
                __import__('{}.{}'.format(cls.__module__, name))
                if not isinstance(interpreters.get(name), JavaScriptInterpreter):
                    raise ImportError('The interpreter was not initialized.')
            except ImportError:
                logging.error('Unable to load {} interpreter'.format(name))
                raise

        return interpreters[name]

    # ------------------------------------------------------------------------------- #

    @abc.abstractmethod
    def eval(self, jsEnv, js):
        pass

    # ------------------------------------------------------------------------------- #

    def solveChallenge(self, body, domain):
        try:
            return float(self.eval(body, domain))
        except Exception:
            logging.error('Error executing Cloudflare IUAM Javascript. {}'.format(BUG_REPORT))
            raise
