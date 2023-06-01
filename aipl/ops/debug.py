from typing import List
import sys

from aipl import defop, LazyRow, UserAbort, Table, AIPL


@defop('debug', None, None, arity=0)
def op_debug(aipl, *args):
    'set debug flag and call breakpoint() before each command'
    aipl.options.debug = True

def _vd_singlestep(aipl, inputs:List[LazyRow], cmd):
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


def stderr_rich(*args):
    import rich
    rich.print(*args, file=sys.stderr)


def install_rich(*args):
    import rich
    AIPL.pre_command = lambda aipl, t, cmd: stderr_rich(t, cmd)


def _rich_table(t:Table, console, console_options):
    import rich
    import rich.table

    table = rich.table.Table(show_header=True, show_lines=True, header_style="bold magenta")
    colnames = [c.name for c in t.columns if not c.hidden or c is t.current_col]
    for colname in colnames:
        table.add_column(colname)
    for row in t:
        rowdata = []
        for colnames in colnames:
            cell = row[colname]
            if not isinstance(cell, (Table, str, int, float)):
                cell = str(cell)
            rowdata.append(cell)
        table.add_row(*rowdata)
    return [table]


Table.__rich_console__ = _rich_table
AIPL.step_rich = install_rich
AIPL.step_vd = _vd_singlestep
