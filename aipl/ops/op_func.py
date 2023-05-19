from copy import copy
from typing import List, Dict
from collections import defaultdict

from aipl import defop
from aipl.table import Table, LazyRow, Column

@defop('group', 1.5, 1.5)
def op_group(aipl, t:Table):
    r = defaultdict(list)
    for row in t:
        r[row.value].append(row._row)

    for k, v in r.items():
        ret = Table([])
        ret.rows = v
        yield dict(key=k, items=ret)


@defop('python',-1,-1,0)
def op_python(aipl, prompt=''):
    exec(prompt)


@defop('take', 1.5, 1.5)
def op_take(aipl, t:Table, n=1):
    ret = copy(t)
    ret.rows = t.rows[:n]
    return ret


@defop('unravel', 2, 1.5)
def op_unravel(aipl, v:Table) -> Table:
    ret = Table()
    ret.rows = []
    newkey = aipl.unique_key
    for row in v: # row:LazyRow
        for row_two in row.value:
            ret.rows.append({'__parent':row_two, newkey:row_two.value})

    ret.add_column(Column(newkey))
    return ret


@defop('filter', 1.5, 1.5)
def op_filter(aipl, t:Table):
    ret = copy(t)
    ret.rows = [r._row for r in t if r.value]
    ret.columns = ret.columns[:-1]  # discard bool column
    return ret
