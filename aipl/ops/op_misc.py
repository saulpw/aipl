from copy import copy
from typing import List

from aipl import defop, Table, LazyRow, AIPLException
from aipl.utils import stderr


@defop('sample', 1.5, 1.5)
def op_sample(aipl, t:Table, n:int=1):
    import random
    return Table(random.sample(t.rows, n), parent=t)


class UserAbort(BaseException):
    pass

@defop('abort', None, None, arity=0)
def op_abort(aipl, *args):
    raise UserAbort(*args)


@defop('debug', None, None, arity=0)
def op_debug(aipl, *args):
    aipl.debug = True
    aipl.single_step = lambda *args, **kwargs: breakpoint()


def vd_singlestep(inputs:List[LazyRow], cmd):
    import visidata
    @visidata.VisiData.api
    def uberquit(vd):
        raise UserAbort('user abort')

    inputs = list(r._asdict() for r in inputs)
    sheet = visidata.PyobjSheet('current_input', source=inputs)
    sheet.help = '{sheet.recentcmd}'
    argstr = ' '.join(str(x) for x in cmd.args)
    kwargstr = ' '.join(f'{k}={v}' for k, v in cmd.kwargs.items())
    sheet.recentcmd = f'[line {cmd.linenum}] !' + ' '.join([cmd.opname, argstr, kwargstr])
    sheet.addCommand('Q', 'quit-really', 'uberquit()')
    visidata.vd.run(sheet)


@defop('debug-vd', None, None, arity=0)
def op_debug_vd(aipl):
    aipl.single_step = vd_singlestep


@defop('assert-equal', 0, None)
def op_assert_equal(aipl, v:str, prompt=''):
    if v != prompt:
        raise AIPLException(f'assert failed! value not equal\n  ' + v)


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


@defop('comment', None, None, arity=0)
def op_comment(aipl, *args, **kwargs):
    pass
