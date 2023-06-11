
from dataclasses import dataclass

@dataclass
class Error:
    'A cascading error that does not break the pipeline'
    linenum:int = 0
    opname:str = ''
    exception:Exception = None

    def __str__(self):
        return f'AIPL Error (line {self.linenum} !{self.opname}): {self.exception}'

    def __getitem__(self, k):
        return self


class AIPLCompileError(Exception):
    'A nice error message during compilation to print to stderr and exit without a stacktrace.'

class AIPLException(Exception):
    'A nice error message to print to stderr and exit without a stacktrace.'


class UserAbort(BaseException):
    'UserAbort not caught by internal error handling; will always exit.'


from .utils import stderr
from .db import Database
from .table import Table, Column, LazyRow
from .interpreter import AIPL, defop, Command
from .caching import expensive, dbcache
from .parser import parse
from .main import main


def import_submodules(pkgname):
    'Import all files below the given *pkgname*'
    import pkgutil
    import importlib

    m = importlib.import_module(pkgname)
    for module in pkgutil.walk_packages(m.__path__):
        importlib.import_module(pkgname + '.' + module.name)


import_submodules('aipl.ops')
