import sys
import traceback

from aipl import defop, InnerPythonException


def inner_exec(obj, *args, **kwargs):
    try:
        return exec(obj, *args, **kwargs)
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb = traceback.extract_tb(exc_traceback)
        raise InnerPythonException(exc_value, tb[1:], obj)


def inner_eval(obj, *args, **kwargs):
    try:
        return eval(obj, *args, **kwargs)
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb = traceback.extract_tb(exc_traceback)
        raise InnerPythonException(exc_value, tb[1:], obj)


@defop('python',0,None)
def op_python(aipl, prompt:str=''):
    'exec() Python toplevel statements.'
    inner_exec(prompt, aipl.globals)


@defop('python-expr', 0.5, 0, rankin2=0)
def op_python_expr(aipl, row, expr:str):
    'Add columns for Python expressions.'
    return inner_eval(expr, aipl.globals, row)


@defop('python-input', 0, 1.5)
def op_python_input(aipl, prompt:str=''):
    'eval() Python expression and use as toplevel input table.'
    return inner_eval(prompt, aipl.globals)
