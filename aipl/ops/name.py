from copy import copy

from aipl import defop, Table


@defop('name', 1.5, 1.5)
def op_name(aipl, t:Table, name) -> Table:
    'Rename current input column to given name.'
    ret = copy(t)
    ret.rows = copy(t.rows)
    c = ret.current_col
    c.name = name
    return ret
