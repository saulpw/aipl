from .utils import stderr
from .interpreter import AIPL, defop, AIPLException, UserAbort, Command
from .db import Database, expensive, dbcache
from .table import Table, LazyRow
from .main import main


def import_submodules(pkgname):
    'Import all files below the given *pkgname*'
    import pkgutil
    import importlib

    m = importlib.import_module(pkgname)
    for module in pkgutil.walk_packages(m.__path__):
        importlib.import_module(pkgname + '.' + module.name)


import_submodules('aipl.ops')
