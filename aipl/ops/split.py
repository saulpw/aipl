from aipl import defop

from typing import List

@defop('split', 0, 1)
def op_split(aipl, v: str, maxsize:int=0, sep=None) -> List[str]:
    'Split text into chunks based on sep, keeping each chunk below maxsize.'
    win = []
    tot = 0
    for i, unit in enumerate(v.split(sep)):
        n = len(unit)
        if tot+n > maxsize:
            if win:
                yield (sep or ' ').join(win)
                win = []
                tot = 0

        win.append(unit)
        tot += n

    if win:
        yield (sep or ' ').join(win)


@defop('split-into', 0, 0.5)
def op_split_into(aipl, v:str, *args, sep=None) -> dict:
    return dict(zip(args, v.split(sep)))

def test_split_join(aipl):
    t = aipl.run('!split !take 3 !join', 'now is the time')
    assert len(t.rows) == 1
    assert t[0].value == 'now is the'

