from aipl import defop, Table, SubColumn, LazyRow

__test__ = '''
!test-input
a b c
!split>col1
!table t1
!test-input
d e f
!split>col2
!cross <<t1
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


@defop('cross', 0.5, 1.5, rankin2=100)
def op_cross(aipl, row:LazyRow, t:Table) -> Table:
    'Construct cross-product of left and right inputs (pass right input via `<<tablename`).'
    ret = Table()
    for tright in iterate_tables(t):
        for rightrow in tright:
            ret.rows.append(dict(__parent=row, left=row._row, right=rightrow._row))

    # left columns are available automatically or from __parent
    for c in tright.columns:
        ret.add_column(SubColumn('right', c))

    return ret
