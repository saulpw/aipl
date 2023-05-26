'''
!sample <n>

Replace input table with table of n sampled rows.
'''

from aipl import defop, Table


@defop('sample', 1.5, 1.5)
def op_sample(aipl, t:Table, n:int=1) -> Table:
    'Sample n rows from the input table.'
    import random
    return Table(random.sample(t.rows, n), parent=t)


def test_sample(aipl):
    r = aipl.run('!split !sample 2', 'a b c', 'd e f')
    assert len(r[0]) == 2
    for row in r[0]:
        assert row.value in 'abc'
    for row in r[1]:
        assert row.value in 'def'
