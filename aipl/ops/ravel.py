from typing import List
from copy import copy


from aipl import defop
from aipl.table import Table, Column


@defop('ravel', 100, 1.5)
def op_ravel(aipl, v:Table, rank=0) -> Table:
    'All of the leaf scalars in the value column become a single 1-D array.'
    def _ravel(t:Table, newkey:str, parent=None) -> List['Scalar']:
        for row in t:
            if isinstance(row.value, Table) and row.value.rank > rank:
                yield from _ravel(row.value, newkey, parent=row)
            else:
                if '__parent' not in row._row and parent is not None:
                    row._row['__parent'] = parent

                yield row

    newkey = aipl.unique_key
    ret = Table(parent=v)
    for row in _ravel(v, newkey):
        ret.rows.append(row._row)

        for c in row._table.columns:
            ret.add_column(copy(c))
    return ret


def test_ravel(aipl):
    t = aipl.run_test('!split !take 2 !ravel !join', 'a b c d', 'e f g')
    assert t[0].value == 'a b e f'
