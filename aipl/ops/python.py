from aipl import defop


@defop('python',None,None,0)
def op_python(aipl, prompt:str=''):
    'exec() Python toplevel statements.'
    exec(prompt)


@defop('python-input', 100, 1.5, outcols='pyval')
def op_python_input(aipl, t:'Table', prompt:str=''):
    'eval() Python expression and use as toplevel input table.'
    aipl.globals.update(dict(aipl=aipl))
    return eval(prompt, aipl.globals)
