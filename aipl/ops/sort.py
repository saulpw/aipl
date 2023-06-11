from copy import copy

from aipl import defop, Table


@defop('sort', 1.5, 1.5)
def op_sort(aipl, t:Table, *args):
    ret = copy(t)
    cols = [t.get_column(cname) for cname in args] or [t.current_col]
    ret.rows = sorted(t.rows, key=lambda r: tuple(c.get_value(r) for c in cols))
    return ret


@defop('grade-up', 1.5, 1)
def op_grade_up(aipl, t:Table, *args):
    values = t.values
    return sorted(range(len(values)), key=values.__getitem__)


def test_sort(aipl):
    r = aipl.run_test('!sort', 3,1,4,2,8,5)
    assert r.values == [1,2,3,4,5,8]

def test_grade_up(aipl):
    r = aipl.run_test('!grade-up', 3,1,4,2,8,5)
    assert r.values == [1, 3, 0, 2, 5, 4]
