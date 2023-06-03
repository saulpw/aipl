from aipl import defop

@defop('replace', 0, 0)
def op_replace(aipl, s:str, find:str, repl:str) -> str:
    return s.replace(find, repl)

