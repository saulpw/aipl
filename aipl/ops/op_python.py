from aipl import defop


@defop('python',None,None,0)
def op_python(aipl, prompt:str=''):
    'exec() Python toplevel statements.'
    exec(prompt)


@defop('python-input', None, 1.5, 0)
def op_python(aipl, prompt:str=''):
    'eval() Python expression and use as toplevel input table.'
    aipl.globals.update(dict(aipl=aipl))
    return eval(prompt, aipl.globals)
