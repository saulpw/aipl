'''
!take `n` returns a copy of an input `Table` with only the first `n` rows.
'''

from copy import copy

from aipl import defop
from aipl.table import Table

@defop('take', 1.5, 1.5)
def op_take(aipl, t:Table, n=1) -> Table:
    'Return a table with first n rows of `t`'
    ret = copy(t)
    ret.rows = t.rows[:n]
    return ret


def test_take(aipl):
    r = aipl.run('!take 2', '1 2 3', '4 5 6', '7 8 9')
    assert len(r.rows) == 2
    assert r[0].value == '1 2 3'
    assert r[1].value == '4 5 6'
