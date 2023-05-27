from aipl import defop, AIPLException


@defop('assert-equal', 0, None)
def op_assert_equal(aipl, v:str, prompt=''):
    'Error if value is not equal to prompt.'
    if v != prompt:
        raise AIPLException(f'assert failed! value not equal:\n' + v)
