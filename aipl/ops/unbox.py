from aipl import defop, Table


@defop('unbox', 1.5, 1.5)
def op_unbox(aipl, t:Table) -> Table:
    'Return value of single-row table (remove outermost layer).'
    assert len(t) == 1
    return Table(t[0].value)
