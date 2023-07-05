from collections import ChainMap

from aipl import defop, LazyRow

@defop('format', 0.5, 0, rankin2=0)
def op_format(aipl, row:LazyRow, prompt:str='') -> str:
    'Format prompt text (right operand) as a Python string template, substituting values from row (left operand) and global context.'
    return prompt.format_map(ChainMap(row, aipl.tables, aipl.globals))
