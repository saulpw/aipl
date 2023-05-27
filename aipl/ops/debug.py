from typing import List

from aipl import defop, LazyRow, UserAbort


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
