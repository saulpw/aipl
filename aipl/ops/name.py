from copy import copy

from aipl import defop, Table


@defop('name', 1.5, 1.5)
def op_name(aipl, t:Table, name) -> Table:
    'Rename current input column to given name.'
    ret = copy(t)
    c = ret.columns[-1]
    c.name = name
    return ret
