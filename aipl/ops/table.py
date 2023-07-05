from aipl import defop, Table, alias


@defop('table', 100, 1.5)
def op_table(aipl, t:Table, tname:str) -> Table:
    'Save toplevel input into global list of tables.'
    aipl.tables[tname] = t
    return t


alias('global', 'table')
