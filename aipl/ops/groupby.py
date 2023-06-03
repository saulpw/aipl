'''
!groupby <colname...>

Group rows by given named columns, with output value for each key being table of corresponding rows.
'''

from copy import copy
from collections import defaultdict

from aipl import defop
from aipl.table import Table, Column


@defop('groupby', 1.5, 1.5)
def op_groupby(aipl, t:Table, *args) -> Table:
    'Group rows into tables, by set of columns given as args.'
    groups = defaultdict(list)  # groupkey -> list of rowdict
    for row in t:
        k = tuple([row[colname] for colname in args])
        groups[k].append(row._row)

    ret = Table()

    newkey = aipl.unique_key
    for key, rows in groups.items():
        outdict = dict(zip(args, key))
        outtable = copy(t)
        outtable.rows = rows
        outdict[newkey] = outtable
        ret.rows.append(outdict)

    for colname in args:
        ret.add_column(Column(colname, colname))

    ret.add_column(Column(newkey))
    return ret


def test_groupby(aipl):
    r = aipl.run('!split-into name num  !groupby name', 'Bob 4', 'Alice 3', 'Carol 8', 'Bob 2', 'Alice 5', 'Bob 1')
    assert len(r) == 3
