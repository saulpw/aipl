from copy import copy

from aipl import defop, Table, alias, Column


@defop('sort', 1.5, 1.5)
def op_sort(aipl, t:Table, *args):
    'Sort the table by the given columns.'
    ret = copy(t)
    cols = [t.get_column(cname) for cname in args] or [t.current_col]
    ret.rows = sorted(t.rows, key=lambda r: tuple(c.get_value(r) for c in cols))
    return ret


@defop('grade-up', 1.5, 1)
def op_grade_up(aipl, t:Table, *args):
    'Assign ranks to unique elements in an array, incrementally increasing each by its corresponding rank value.'
    values = t.values
    return sorted(range(len(values)), key=values.__getitem__)

@defop('incr', 1.5, 1.5)
def op_incr(aipl, t:Table, step:int= 1, base:int=1, *args):
    'Add column that starts at base `base` incrementing by `step` for each row in `t`.'
    incr_values = [base + x*step for x in range(len(t.rows))]
    ret = copy(t)
    ret.rows = []
    for i, row in enumerate(t.rows):
        row['incr'] = incr_values[i]
        ret.rows.append(row)

    ret.add_column(Column('incr'))

    return ret


def test_sort(aipl):
    r = aipl.run_test('!sort', 3,1,4,2,8,5)
    assert r.values == [1,2,3,4,5,8]

def test_grade_up(aipl):
    r = aipl.run_test('!grade-up', 3,1,4,2,8,5)
    assert r.values == [1, 3, 0, 2, 5, 4]

def test_incr(aipl):
    r = aipl.run_test('!incr', 3, 1, 4, 2, 8, 5)
    assert r.values == [1, 2, 3, 4, 5, 6]

alias('order-by', 'sort')
