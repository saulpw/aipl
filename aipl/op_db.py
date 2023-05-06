from typing import List, Dict

from .utils import stderr
from .interpreter import defop, expensive


@defop('dbinsert', 0.5, -1, 1)
def op_dbinsert(aipl, row, tblname, **kwargs):
    aipl.insert(tblname, **row._asdict(), **kwargs)
