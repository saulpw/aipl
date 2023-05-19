from copy import copy

from aipl import defop, Table


@defop('sample', 1.5, 1.5)
def op_sample(aipl, t:Table, n:int=1):
    import random
    return Table(random.sample(t.rows, n), parent=t)


class Abort(BaseException):
    pass

@defop('abort', -1, -1, arity=0)
def op_abort(aipl):
    raise Abort(f'deliberately aborted')


@defop('debug', -1, -1, arity=0)
def op_debug(aipl, *args):
    aipl.debug = True
    aipl.single_step = lambda *args, **kwargs: breakpoint()


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
        stderr(f'no such column {name}')
    t.columns.remove(col)
    t.add_column(col)
    return t
