from typing import List
from copy import copy


from aipl import defop
from aipl.table import Table, Column


@defop('ravel', 100, 1.5)
def op_ravel(aipl, v:Table) -> Table:
    def _ravel(t:Table, newkey:str) -> List['Scalar']:
        for row in t:
            if isinstance(row.value, Table):
                yield from _ravel(row.value, newkey)
            else:
                yield row

    newkey = aipl.unique_key
    ret = Table()
    for row in _ravel(v, newkey):
        ret.rows.append(row._row)

    for c in row._table.columns:
        ret.add_column(copy(c))
    return ret


def test_ravel(aipl):
    t = aipl.run('!split !take 2 !ravel !join', 'a b c d', 'e f g')
    assert t[0] == 'a b e f'
