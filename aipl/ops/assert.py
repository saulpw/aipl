'''
!assert- used for cwenforcing a check in a .aipl script.
'''

import json

from aipl import defop, AIPLException, Table


@defop('assert-equal', 0, None)
def op_assert_equal(aipl, v:str, prompt=''):
    'Error if value is not equal to prompt.'
    if v != prompt:
        raise AIPLException(f'assert failed! value not equal:\n' + v)

@defop('assert-json', 100, None)
def op_assert_json(aipl, t:Table, prompt:str=''):
    'Error if value Column is not equal to json blob in prompt.'
    if t._asdict() != json.loads(prompt):
        jsonenc = _jsonEncoder()
        raise AIPLException(f'assert failed! value not equal\n  ' + jsonenc.encode(t._asdict()))
