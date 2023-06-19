#!/usr/bin/env python3

import sys
from aipl import AIPL


def dialectize(cmd:Command) -> str:
    ret = f'!{cmd.opname}'
    if cmd.args:
        ret += ' ' + ' '.join(str(arg) for arg in cmd.args)
    if cmd.kwargs:
        ret += ' ' + ' '.join(f'{k}={v}' for k,v in cmd.kwargs.items())

    ret += '\n'
    if cmd.prompt:
        ret += cmd.prompt + '\n\n'
    return ret


def main(*args):
    aipl = AIPL()
    for fn in args:
        code = open(fn).read()
        with open(fn, 'w') as outfp:
            cmds = aipl.parse(code)
            for cmd in cmds:
                # XXX: need to handle comments and outputting a particular dialect
                print(dialectize(cmd), file=outfp)


main(*sys.argv[1:])
