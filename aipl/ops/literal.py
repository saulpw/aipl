from aipl import defop

@defop('literal', None, 0, 0)
def op_literal(aipl, prompt=''):
    return prompt
