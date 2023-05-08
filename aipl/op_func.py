from copy import copy
from typing import List, Dict
from collections import defaultdict

from .utils import stderr
from .interpreter import defop
from .table import Table, LazyRow

@defop('group', 1.5, 1.5)
def op_group(aipl, t:Table):
    r = defaultdict(list)
    for row in t:
        r[row.value].append(row._row)

    for k, v in r.items():
        ret = Table([])
        ret.rows = v
        yield dict(key=k, items=ret)


@defop('take', 1.5, 1.5)
def op_take(aipl, t:Table, n=1):
#    ret = copy(t)
#    ret.rows = t.rows[:n]
#    return ret
    return Table(t.rows[:n])


def _unravel(t:Table):
    for row in t:
        if isinstance(row.value, Table):
            yield from _unravel(row.value)
        else:
            yield dict(value=row.value)


@defop('unravel', 1.5, 1.5)
def op_unravel(aipl, v:Table, sep=' '):
    return Table(list(_unravel(v)))


@defop('filter', 1.5, 1.5)
def op_filter(aipl, t:Table):
    ret = copy(t)
    ret.rows = [r._row for r in t if r.value]
    ret.columns = ret.columns[:-1]  # discard bool column
    return ret
