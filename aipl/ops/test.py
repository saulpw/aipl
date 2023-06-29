'''
!test- used for testing .aipl scripts.
'''

import json

from aipl import defop, AIPLException, Table

@defop('test-input', 100, 1.5, rankin2=0)  # immed
def op_test_input(aipl, t:Table, prompt=''):
    'In test mode, replace input with prompt.'
    if aipl.options.test:
        return aipl.new_input(prompt)
    return t


@defop('test-equal', 0, None, rankin2=0)
def op_test_equal(aipl, v:str, prompt=''):
    'In test mode, error if value is not equal to prompt.'
    if aipl.options.test:
        if v != prompt:
            raise AIPLException(f'assert failed! value not equal:\n' + v)


@defop('test-json', 100, None, rankin2=0)
def op_test_json(aipl, t:Table, prompt:str=''):
    'Error if value Column is not equal to json blob in prompt.'

    class _jsonEncoder(json.JSONEncoder):
        def default(self, obj):
            return str(obj)

    if t._asdict() != json.loads(prompt):
        jsonenc = _jsonEncoder()
        raise AIPLException(f'assert failed! value not equal\n  ' + jsonenc.encode(t._asdict()))
