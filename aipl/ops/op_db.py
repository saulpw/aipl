from aipl import defop


@defop('dbinsert', 0.5, None, 1)
def op_dbinsert(aipl, row, tblname, **kwargs):
    'Insert each row into database table.'
    aipl.insert(tblname, **row._asdict(), **kwargs)


@defop('dbdrop', None, None, 0)
def op_dbdrop(aipl, tblname):
    'Drop database table.'
    aipl.sql(f'DROP TABLE IF EXISTS {tblname}')
