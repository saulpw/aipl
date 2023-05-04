import os
import sys

from .interpreter import AIPLInterpreter
from .op_text import *
from .op_web import *
from .op_llm import *
from .op_misc import *


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
