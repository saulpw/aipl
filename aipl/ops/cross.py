from aipl import defop, Table, SubColumn, LazyRow


def iterate_tables(t:Table, rankin=1):
    if t.rank <= rankin:
        yield t
    else:
        for row in t:
            yield from iterate_tables(row.value, rankin=rankin)


@defop('cross', 0.5, 1.5)
def op_cross(aipl, row:LazyRow, tname:str) -> Table:
    'Construct cross-product of current input with given global table'
    newkey = aipl.unique_key
    ret = Table()
    tleft = row._table

    for tright in iterate_tables(aipl.globals[tname]):
        for rightrow in tright:
            ret.rows.append(dict(left=row._row, right=rightrow._row))

    for c in tleft.columns:
        ret.add_column(SubColumn('left', c.name, c))

    for c in tright.columns:
        ret.add_column(SubColumn('right', c.name, c))

    return ret


@defop('global', 100, 1.5)
def op_global(aipl, t:Table, tname:str) -> Table:
    'Save toplevel input into globals.'
    aipl.globals[tname] = t
    return t
