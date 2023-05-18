from . import defop

@defop('assert-equals', 0, -1)
def op_assert_equals(aipl, v:str, prompt=''):
    assert v == prompt, v
