from aipl import defop, Table, AIPLException


@defop('ref', 1.5, 1.5)
def op_ref(aipl, t:Table, name):
    'Move column on table to end of columns list (becoming the new .value)'
    col = t.get_column(name)
    if col not in t.columns:
        raise AIPLException(f'no such column {name}')

    t.columns.remove(col)
    t.add_column(col)
    return t
