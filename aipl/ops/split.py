from aipl import defop

from typing import List

@defop('split', 0, 1)
def op_split(aipl, v: str, sep:str=None, maxsize:int=0) -> List[str]:
    'Split text into chunks based on sep, keeping each chunk below maxsize.'
    win = []
    tot = 0
    for i, unit in enumerate(v.split(sep)):
        n = len(unit)
        if tot+n > int(maxsize):
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
    'Split text by sep into the given column names.'
    return dict(zip(args, v.split(sep)))

def test_split_join(aipl):
    t = aipl.run_test('!split !take 3 !join', 'now is the time')
    assert len(t.rows) == 1
    assert t[0].value == 'now is the'

