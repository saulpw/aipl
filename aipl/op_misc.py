from typing import List

from .interpreter import defop
from .table import Table


@defop('sample', 1.5, 1.5)
def op_sample(aipl, t:Table, n:int=1):
    import random
    return Table(random.sample(t.rows, n))
