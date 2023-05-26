from typing import List


from aipl import defop
from aipl.table import Table, Column


@defop('ravel', 100, 1.5)
def op_ravel(aipl, v:Table) -> Table:
    def _ravel(t:Table, newkey:str) -> List['Scalar']:
        for row in t:
            if isinstance(row.value, Table):
                yield from _ravel(row.value, newkey)
            else:
                yield {'__parent':row, newkey:row.value}

    newkey = aipl.unique_key
    ret = Table()
    for r in _ravel(v, newkey):
        ret.rows.append(r)
    ret.add_column(Column(newkey))
    return ret
