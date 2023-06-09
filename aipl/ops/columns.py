'''
!column takes a space-seperated list of columns
in the current table, and returns a copy of the table
with only those columns.
Akin to SQLite SELECT.
'''

from copy import copy

from aipl import defop, Table, Column


@defop('columns', 1.5, 1.5)
def op_columns(aipl, t:'Table', *colnames, **renamedcols) -> Table:
    'Create new table containing only these columns.'
    namings = [(n,n) for n in colnames]  # from_name:to_name
    namings.extend((v,k) for k,v in renamedcols.items())
    newcols = []
    ret = copy(t)
    ret.rows = []
    for row in t:
        d = {'__parent':row}
        d.update({to_name:row[from_name] for from_name, to_name in namings})
        ret.rows.append(d)

    for from_name, to_name in namings:
        ret.add_column(Column(to_name))

    return ret

def test_columns(aipl):
    r = aipl.run('!name letters !split !ravel !columns letters', 'a b c', 'd e f')
    assert r[0].value == 'a b c'
    assert r[3].value == 'd e f'
    assert len(r) == 6
