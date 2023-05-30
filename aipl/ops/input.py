'''
!require-input prompts the user for input, if none provided in the script.
'''

import sys

from aipl import defop, Table


@defop('require-input', 100, 100)
def op_require_input(aipl, t:'Table', prompt=''):
    'Ensure there is any input at all; if not, display the prompt and read input from the user.'
    if len(t.rows) == 0 or not t[0]:
        print(prompt, file=sys.stderr)
        print('Ctrl+D to end input', file=sys.stderr)
        return Table([{'input':sys.stdin.read().strip('\n')}])
    return t
