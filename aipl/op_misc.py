from typing import List

from .interpreter import defop


@defop('choose', 1, 0, 1)
def op_choose(aipl, v:List[str], n:int=1):
    import random
    return random.sample(v, n)
