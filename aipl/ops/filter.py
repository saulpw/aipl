'''
!filter returns the table, containing only the rows
that were truthy in the value column.
The value column is then discarded.
'''
from copy import copy

from aipl import defop
from aipl.table import Table

@defop('filter', 1.5, 1.5)
def op_filter(aipl, t:Table) -> Table:
    'Return copy of table, keeping only rows whose value is Truthy.'
    ret = copy(t)
    ret.rows = [r._row for r in t if r.value]
    ret.columns = ret.columns[:-1]  # discard bool column
    return ret

def test_filter(aipl):
    r = aipl.run('!match ^c !filter', 'a b c', 'b c d', 'c d e')
    assert len(r.rows) == 1
    assert r[0].value == 'c d e'
