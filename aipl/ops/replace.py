from aipl import defop

@defop('replace', 0, 0)
def op_replace(aipl, s:str, find:str, repl:str) -> str:
    'Replace `find` in all leaf values with `repl`.'
    return s.replace(find, repl)

