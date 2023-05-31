import os
import sys
import argparse

from aipl import AIPL, Table, UserAbort

def parse_args(args):
    parser = argparse.ArgumentParser(description='AIPL interpreter')
    parser.add_argument('--debug', '-d', action='store_true', help='abort on exception')
    parser.add_argument('--step', action='store', default='', help='call aipl.step_<func>(cmd, input) before each step')
    parser.add_argument('--step-breakpoint', '-x', action='store_const', dest='step', const='breakpoint', help='breakpoint() before each step')
    parser.add_argument('--step-rich', '-v', action='store_const', dest='step', const='rich', help='output rich table before each step')
    parser.add_argument('--step-vd', '--vd', action='store_const', dest='step', const='vd', help='open VisiData with input before each step')
    parser.add_argument('--dry-run', '-n', action='store_true', help='do not execute @expensive operations')
    parser.add_argument('script_or_global', nargs='+', help='scripts to run, or k=v global parameters')
    return parser.parse_args(args)



def main():

    args = parse_args(None)
    global_parameters = {}
    scripts = []

    for arg in args.script_or_global:
        if '=' in arg:
            key, value = arg.split('=', maxsplit=1)
            global_parameters[key] = value
        else:
            scripts.append(arg)

    if not scripts:
        print('no script on stdin: nothing to do', file=sys.stderr)
        return

    aipl = AIPL('aipl-cache.sqlite', **vars(args))

    # dup stdin/stdout if necessary

    if not sys.stdin.isatty():
        try:
            fin = open('/dev/tty')
            aipl.stdin = open(os.dup(0))
            os.dup2(fin.fileno(), 0)
            stdin_contents = aipl.stdin.read()
            fin.close()
        except OSError as e:
            aipl.stdin = sys.stdin
            stdin_contents = ''
    else:
        aipl.stdin = sys.stdin
        stdin_contents = ''

    if not sys.stdout.isatty():
        try:
            fout = open('/dev/tty', mode='w')
            aipl.stdout = open(os.dup(1), 'w')  # for dumping to stdout from interface
            os.dup2(fout.fileno(), 1)
            fout.close() # close file descriptors for original stdin/stdout
        except OSError as e:
            aipl.stdout = sys.stdout
    else:
        aipl.stdout = sys.stdout

    aipl.globals = global_parameters

    for fn in scripts:
        try:
            aipl.run(open(fn).read(), stdin_contents.strip())
        except UserAbort as e:
            print(f'aborted', e, file=sys.stderr)

