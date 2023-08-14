import time

from aipl import defop

@defop('sleep', 0, 0)
def _(aipl, n:float) -> float:
    time.sleep(n)
    return n
