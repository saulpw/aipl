from aipl import defop, Table, SubColumn, LazyRow

__test__ = '''
!test-input
a b c
!split>col1
!global t1
!test-input
d e f
!split>col2
!cross>t2 t1
!format
  {col1}/{col2}
!ravel
!join
!test-equal
a/d b/d c/d a/e b/e c/e a/f b/f c/f
'''

def test_cross(aipl):
    aipl.run_test(__test__)


def iterate_tables(t:Table, rankin=1):
    if t.rank <= rankin:
        yield t
    else:
        for row in t:
            yield from iterate_tables(row.value, rankin=rankin)


@defop('cross', 0.5, 1.5)
def op_cross(aipl, row:LazyRow, tname:str) -> Table:
    'Construct cross-product of current input with given global table'
    ret = Table()
    tleft = row._table

    for tright in iterate_tables(aipl.globals[tname]):
        for rightrow in tright:
            ret.rows.append(dict(left=row._row, right=rightrow._row))

    for c in tleft.columns:
        ret.add_column(SubColumn('left', c.name, c))

    for c in tright.columns:
        ret.add_column(SubColumn('right', c.name, c))

    return ret


@defop('global', 100, 1.5)
def op_global(aipl, t:Table, tname:str) -> Table:
    'Save toplevel input into globals.'
    aipl.globals[tname] = t
    return t
