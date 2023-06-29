from aipl import defop, alias


@defop('nop', None, None)
def op_nop(aipl):
    'No operation.'
    pass


#@defop('identity', 0, 0)
#def op_identity(aipl, v):
#    return v
alias('identity', 'nop')  # functionally equivalent in AIPL
