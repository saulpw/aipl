from copy import copy
from typing import List, Dict
from collections import defaultdict

from aipl import defop
from aipl.table import Table, LazyRow, Column, ParentColumn

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
    ret = copy(t)
    ret.rows = t.rows[:n]
    return ret


@defop('ravel', 100, 1.5)
def op_ravel(aipl, v:Table) -> Table:
    def _ravel(t:Table, newkey:str) -> List['Scalar']:
        for row in t:
            if isinstance(row.value, Table):
                yield from _ravel(row.value, newkey)
            else:
                yield {'__parent':row, newkey:row.value}

    newkey = aipl.unique_key
    ret = Table()
    for r in _ravel(v, newkey):
        ret.rows.append(r)
    ret.add_column(Column(newkey))
    return ret


@defop('def', None, None, arity=0)  # immediate
def op_def(aipl, opname, prompt=''):
    cmds = aipl.parse(prompt)

    @defop(opname,
           rankin=cmds[0].op.rankin,
           rankout=cmds[-1].op.rankout,
           arity=cmds[0].op.arity)
    def new_operator(aipl, input, *args, **kwargs):
        argkey = aipl.unique_key
        ret = aipl.run_cmdlist(cmds, Table([{argkey:input}]), *args)
        return ret[0]
