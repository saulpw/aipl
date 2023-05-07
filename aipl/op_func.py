from typing import List, Dict
from collections import defaultdict

from .utils import stderr
from .interpreter import defop
from .table import Table

@defop('group', 2, 2, 1)
def op_group(aipl, t:Table):
    r = defaultdict(list)
    for row in t:
        r[row.value].append(row._row)

    for k, v in r.items():
        ret = Table([])
        ret.rows = v
        yield dict(key=k, items=ret)


@defop('take', 2, 2, 1)
def op_take(aipl, t:Table, n=1):
    return Table(t.rows[:n])
