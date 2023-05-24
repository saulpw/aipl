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


@defop('unravel', 2, 1.5)
def op_unravel(aipl, v:Table) -> Table:
    ret = Table()
    ret.rows = []
    newkey = aipl.unique_key
    for row in v: # row:LazyRow
        for row_two in row.value:
            ret.rows.append({'__parent':row_two, newkey:row_two.value})

    for c in v.columns:
        ret.add_column(ParentColumn(c.name, c))
    ret.add_column(Column(newkey))
    return ret


@defop('filter', 1.5, 1.5)
def op_filter(aipl, t:Table):
    ret = copy(t)
    ret.rows = [r._row for r in t if r.value]
    ret.columns = ret.columns[:-1]  # discard bool column
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
