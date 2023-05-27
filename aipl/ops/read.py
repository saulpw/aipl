from aipl import defop


@defop('read', None, 0, arity=0)
def op_read(aipl, v:str) -> str:
    'Open, read, and return contents in given local filename.'
    return open(v).read()
