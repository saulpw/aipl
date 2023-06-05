class AIPLException(Exception):
    'A nice error message to print to stderr and exit without a stacktrace.'


class UserAbort(BaseException):
    'UserAbort not caught by internal error handling; will always exit.'


from .utils import stderr
from .db import Database
from .table import Table, Column, LazyRow
from .interpreter import AIPL, defop, Command
from .caching import expensive, dbcache
from .main import main


def import_submodules(pkgname):
    'Import all files below the given *pkgname*'
    import pkgutil
    import importlib

    m = importlib.import_module(pkgname)
    for module in pkgutil.walk_packages(m.__path__):
        importlib.import_module(pkgname + '.' + module.name)


import_submodules('aipl.ops')
