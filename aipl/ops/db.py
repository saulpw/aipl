from aipl import defop, Database


@defop('dbopen', None, 0)
def op_dbopen(aipl, url:str):
    'Open connection to database.'
    return Database(url)

@defop('dbquery', 0.5, 1.5)
def op_dbquery(aipl, row:'LazyRow', dbname:str, tblname:str, *colnames, **kwargs):
    'Query database table.'
    for r in aipl.globals[dbname].select(tblname, **kwargs):
        yield {colname:r[colname] for colname in colnames}


@defop('dbdrop', None, None, 0)
def op_dbdrop(aipl, tblname:str):
    'Drop database table.'
    aipl.output_db.sql(f'DROP TABLE IF EXISTS {tblname}')


@defop('dbinsert', 0.5, None)
def op_dbinsert(aipl, row, tblname:str, **kwargs):
    'Insert each row into database table.'
    aipl.output_db.insert(tblname, **row._asdict(), **kwargs)
