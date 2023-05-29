'''
!column takes a space-seperated list of columns
in the current table, and returns a copy of the table
with only those columns.
Akin to SQLite SELECT.
'''

from aipl import defop


@defop('columns', 1.5, 1.5)
def op_columns(aipl, t:'Table', *colnames):
    'Set table columns to only those named as args.'
    newcols = []
    for name in colnames:
        c = t.get_column(name)
        if not c:
            colnamestr = ','.join(t.colnames)
            raise Exception(f'no column "{name}" in {colnamestr}')

        newcols.append(c)

    t.columns = newcols
    return t
