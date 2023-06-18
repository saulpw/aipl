import sys
import inspect
import readline
import traceback

from aipl import parse, Table, AIPLException


def repl(aipl, inputs:list[Table]):
    'Standard Read-Eval-Print-Loop (REPL)'
    import rich
    def completer(text, state):
        ops = list(aipl.operators.keys()) + list(aipl.aliases.keys())
        text = text[1:]
        results = [x for x in ops if x.startswith(text)]
        if results:
            return "!" + results[state]

    readline.parse_and_bind("tab: complete")
    readline.set_completer_delims(' \n=')
    readline.set_completer(completer)

    while True:
        sys.stdout.flush()
        try:
            cmdtext = input('> ')
        except KeyboardInterrupt as e:
            break  # exit on ^C
        except EOFError:
            print("\n")
            continue

        if not cmdtext.strip():  # do nothing empty line
            continue

        try:
            cmds = parse(cmdtext)
            op = aipl.get_op(cmds[0].opname)
            if 'prompt' in inspect.signature(op).parameters:
                while True:
                    line = sys.stdin.readline()
                    if not line.strip():
                        break
                    cmdtext += '\n' + line

            inputs = aipl.run(cmdtext, inputs)
            rich.print(inputs[-1])
        except AIPLException as e:
            print(e.args[0])
        except Exception as e:
            traceback.print_exc()
