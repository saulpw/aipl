from typing import List, Dict

from .utils import stderr
from .interpreter import defop


@defop('dbinsert', 0.5, -1, 1)
def op_dbinsert(aipl, row, tblname, **kwargs):
    aipl.insert(tblname, **row._asdict(), **kwargs)


@defop('dbdrop', -1, -1, 0)
def op_dbdrop(aipl, tblname):
    aipl.sql(f'DROP TABLE IF EXISTS {tblname}')
