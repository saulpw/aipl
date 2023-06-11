from aipl import defop

from typing import List

@defop('join', 1, 0, 1)
def op_join(aipl, v:List[str], sep=' ') -> str:
    'Join inputs with sep into a single output scalar.'
    return sep.join(v)

def test_toplevel_join(aipl):
    t = aipl.run_test('!join', 'now', 'is', 'the')
    assert len(t.rows) == 1
    assert t[0].value == 'now is the'

