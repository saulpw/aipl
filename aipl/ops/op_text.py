from collections import ChainMap
from typing import List, Dict, Mapping

from aipl import defop
from aipl.table import LazyRow, Table, Column


@defop('format', 0.5, 0)
def op_format(aipl, row:LazyRow, prompt:str='') -> str:
    'Format prompt text as a Python string template, substituting values from row and global context.'
    return prompt.format_map(ChainMap(aipl.globals, row))


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


@defop('join', 1, 0, 1)
def op_join(aipl, v:List[str], sep=' ') -> str:
    'Join inputs with sep into a single output scalar.'
    return sep.join(v)


@defop('print', 0, None, 1)
def op_print(aipl, v:str):
    'Print to stdout.'
    print(v, file=aipl.stdout)

@defop('match', 0, 0, 1)
def op_match(aipl, v:str, regex:str) -> bool:
    'Return a bool with whether value matched regex. Used with !filter.'
    import re
    m = re.search(regex, v)
    return m is not None

@defop('replace', 0, 0)
def op_replace(aipl, s:str, find:str, repl:str) -> str:
    return s.replace(find, repl)


@defop('save', 0, None, 1)
def op_save(aipl, v:str, filename=''):
    'Save to given filename.'
    assert '{' not in filename, filename
    with open(filename, 'w') as fp:
        fp.write(v)


@defop('literal', None, 0, 0)
def op_literal(aipl, prompt=''):
    return prompt
