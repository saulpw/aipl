from collections import ChainMap
from typing import List, Dict, Mapping

from aipl import defop
from aipl.table import LazyRow, Table, Column


@defop('format', 0.5, 0)
def op_format(aipl, row:LazyRow, prompt:str='') -> str:
    'Format prompt text as a Python string template, substituting values from row and global context.'
    return prompt.format_map(ChainMap(aipl.globals, row))


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
