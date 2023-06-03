from typing import List
import sys

from aipl import defop, LazyRow, UserAbort, Table, AIPL, Command


@defop('option', None, None, arity=0)
def op_option(aipl, **kwargs):
    for k, v in kwargs.items():
        aipl.options[k] = v


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


def install_rich(aipl, *args):
    import rich
    AIPL.pre_command = lambda aipl, t, cmd: stderr_rich(t, cmd)


def _rich_table(t:Table, console, console_options):
    import rich
    import rich.table

    table = rich.table.Table(show_header=True,
                             row_styles=['', 'bold'],
                             header_style="bold magenta")
    colnames = []
    for col in t.columns:
        if col.hidden:
            if col is not t.current_col:
                continue
        colname = col.name

        colnames.append(colname)
        table.add_column(colname)

    maxrows = 3
    maxstrlen = 280
    for i, row in enumerate(t):
        if i >= maxrows:
            table.add_row('[... %s more rows ...]' % (len(t) - maxrows))
            break
        rowdata = []
        for colname in colnames:
            cell = row[colname]
            if not isinstance(cell, (Table, str)):
                cell = str(cell)
            if isinstance(cell, str) and len(cell) > maxstrlen:
                cell = cell[:maxstrlen] + ' [...]'
            rowdata.append(cell)
        table.add_row(*rowdata)
    return [table]


def _rich_command(cmd:Command, console, console_options):
    return [str(cmd)]


Table.__rich_console__ = _rich_table
Command.__rich_console__ = _rich_command
AIPL.step_rich = install_rich
AIPL.step_vd = _vd_singlestep
