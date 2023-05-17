from typing import List, Dict, Mapping
from .interpreter import defop
from .table import LazyRow, Table, Column

@defop('format', 0.5, 0)
def op_format(aipl, row:LazyRow, prompt:str='') -> str:
    'Format prompt text as template, substituting values from row'
    return prompt.format_map(row)


@defop('split', 0, 1)
def op_split(aipl, v: str, maxsize:int=0, sep=None) -> List[str]:
    'Split text into chunks based on sep, keeping each chunk below maxsize'
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


@defop('join', 1, 0, 1)
def op_join(aipl, v:List[str], sep=' ') -> str:
    'Join inputs with sep into a single output.'
    return sep.join(v)


@defop('print', 0, 0, 1)
def op_print(aipl, v:str):
    'Print to stdout'
    print(v, file=aipl.stdout)
    return v

@defop('lowercase', 0, 0)
def op_lowercase(aipl, v:str) -> str:
    return v.lower()

@defop('uppercase', 0, 0)
def op_uppercase(aipl, v:str) -> str:
    return v.upper()

@defop('match', 0, 0, 1)
def op_match(aipl, v:str, regex:str) -> bool:
    import re
    m = re.search(regex, v)
    return m is not None


@defop('save', 0, -1, 1)
def op_save(aipl, v:str, filename=''):
    'Save to given filename.'
    assert '{' not in filename, filename
    with open(filename, 'w') as fp:
        fp.write(v)


@defop('literal', -1, 0, 0)
def op_literal(aipl, prompt=''):
    return prompt
