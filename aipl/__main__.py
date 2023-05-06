import os
import sys

from .interpreter import AIPLInterpreter
from .op_text import *
from .op_web import *
from .op_llm import *
from .op_misc import *
from .op_db import *


def duptty():
    'Duplicate stdin/stdout for input/output and reopen tty as stdin/stdout.  Return (stdin, stdout).'
    try:
        fin = open('/dev/tty')
        fout = open('/dev/tty', mode='w')
        stdin = open(os.dup(0))
        stdout = open(os.dup(1))  # for dumping to stdout from interface
        os.dup2(fin.fileno(), 0)
        os.dup2(fout.fileno(), 1)

        # close file descriptors for original stdin/stdout
        fin.close()
        fout.close()
    except Exception as e:
        stdin = sys.stdin
        stdout = sys.stdout

    return stdin, stdout


def vd_singlestep(inputs:List[LazyRow], cmd):
    import visidata
    @visidata.VisiData.api
    def uberquit(vd):
        raise BaseException('user abort')

    inputs = list(r._asdict() for r in inputs)
    sheet = visidata.PyobjSheet('current_input', source=inputs)
    sheet.help = '{sheet.recentcmd}'
    argstr = ' '.join(str(x) for x in cmd.args)
    kwargstr = ' '.join(f'{k}={v}' for k, v in cmd.kwargs.items())
    sheet.recentcmd = '!' + ' '.join([cmd.opname, argstr, kwargstr])
    sheet.addCommand('Q', 'quit-really', 'uberquit()')
    visidata.vd.run(sheet)


def main(*args):
    if not sys.stdin.isatty():
        stdin, stdout = duptty()
    script = stdin.read()

    script = script.strip()
    if not script:
        print('no script on stdin: nothing to do', file=sys.stderr)
        return

    aipl = AIPLInterpreter('aipl-cache.sqlite')
    aipl.run(script, *args)


if __name__ == '__main__':
    main(*sys.argv[1:])
