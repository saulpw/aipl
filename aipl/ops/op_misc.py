from copy import copy
from typing import List

from aipl import defop, Table, LazyRow, AIPLException
from aipl.utils import stderr

class UserAbort(BaseException):
    pass

@defop('abort', None, None, arity=0)
def op_abort(aipl, *args):
    raise UserAbort(*args)

@defop('assert-equal', 0, None)
def op_assert_equal(aipl, v:str, prompt=''):
    if v != prompt:
        raise AIPLException(f'assert failed! value not equal:\n' + v)


@defop('name', 1.5, 1.5)
def op_name(aipl, t:Table, name) -> Table:
    ret = copy(t)
    c = ret.columns[-1]
    c.name = name
    return ret


@defop('ref', 1.5, 1.5)
def op_ref(aipl, t:Table, name):
    'Move column on table to end of columns list (becoming the new .value)'
    col = t.get_column(name)
    if col not in t.columns:
        raise AIPLException(f'no such column {name}')

    t.columns.remove(col)
    t.add_column(col)
    return t
