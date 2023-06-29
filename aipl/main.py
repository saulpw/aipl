import os
import sys
import traceback
import argparse

from aipl import AIPL, Table, UserAbort, AIPLException, parse, repl

def parse_args(args):
    parser = argparse.ArgumentParser(description='AIPL interpreter')
    parser.add_argument('--debug', '-d', action='store_true', help='abort on exception')
    parser.add_argument('--test', '-t', action='store_true', help='enable test mode')
    parser.add_argument('--interactive', '-i', action='store_true', help='interactive REPL')
    parser.add_argument('--step', action='store', default='', help='call aipl.step_<func>(cmd, input) before each step')
    parser.add_argument('--step-breakpoint', '-x', action='store_const', dest='step', const='breakpoint', help='breakpoint() before each step')
    parser.add_argument('--step-rich', '-v', action='store_const', dest='step', const='rich', help='output rich table before each step')
    parser.add_argument('--step-vd', '--vd', action='store_const', dest='step', const='vd', help='open VisiData with input before each step')
    parser.add_argument('--dry-run', '-n', action='store_true', help='do not execute @expensive operations')
    parser.add_argument('--cache-db', '-c', action='store', default='aipl-cache.sqlite', dest='cachedbfn', help='sqlite database for caching operators')
    parser.add_argument('--no-cache', action='store_const', dest='cachedbfn', const='', help='sqlite database for caching operators')
    parser.add_argument('--output-db', '-o', action='store', default='aipl-cache.sqlite', dest='outdbfn', help='sqlite database accessible to !db operators')
    parser.add_argument('--split', '--separator', '-s', action='store', default='\n', dest='separator', help='separator to split input on')
    parser.add_argument('script_or_global', nargs='*', help='scripts to run, or k=v global parameters')
    return parser.parse_args(args)



def main():

    args = parse_args(None)
    global_parameters = {}
    scripts = []
    inputs = []

    for arg in args.script_or_global:
        if '=' in arg:
            key, value = arg.split('=', maxsplit=1)
            global_parameters[key] = value
        else:
            scripts.append(arg)

    if not scripts:  # nothing to run -> REPL
        args.interactive = True

    aipl = AIPL(**vars(args))

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

    aipl.globals.update(global_parameters)

    # add input from stdin
    input_text = stdin_contents.strip()

    if args.separator:
        inputlines = input_text.split(args.separator)
    else:
        inputlines = [input_text]

    inputs.append(aipl.new_input(*inputlines))

    try:
        for fn in scripts:
            inputs = aipl.run(open(fn).read(), inputs)

        if not scripts or args.interactive:
            repl(aipl, inputs)
    except UserAbort as e:
        print(f'aborted', e, file=sys.stderr)
        sys.exit(2)
    except AIPLException as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    finally:
        if aipl.cost_usd:
            print(f'total cost: ${aipl.cost_usd:.02f}', file=sys.stderr)
