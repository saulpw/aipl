from aipl import defop

@defop('print', 0, None, 1)
def op_print(aipl, v:str):
    'Print to stdout.'
    print(v, file=aipl.stdout)

