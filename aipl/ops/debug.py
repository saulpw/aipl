from typing import List

from aipl import defop, LazyRow, UserAbort, Table


@defop('debug', None, None, arity=0)
def op_debug(aipl, *args):
    'set debug flag and call breakpoint() before each command'
    aipl.debug = True
    aipl.single_step = lambda *args, **kwargs: breakpoint()


@defop('debug-vd', None, None, arity=0)
def op_debug_vd(aipl):
    'launch visidata with current input before each command'
    def _vd_singlestep(inputs:List[LazyRow], cmd):
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
    aipl.single_step = _vd_singlestep


@defop('debug-rich', None, None, arity=0)
def op_debug_rich(aipl):
    'Print input table table to stderr (using rich) before each command.'
    import rich
    def _rich_table(t:Table, console, console_options):
        import rich.table

        table = rich.table.Table(show_header=True, header_style="bold magenta")
        for c in t.columns:
            table.add_column(c.name)
        for row in t:
            table.add_row(*[row[c.name] for c in t.columns])
        return [table]

    Table.__rich_console__ = _rich_table
    import sys
    aipl.single_step = lambda t, cmd: rich.print(t, file=sys.stderr)
