from aipl import defop

@defop('literal', None, 0)
def op_literal(aipl, prompt=''):
    'Set prompt as top-level input, without formatting.'
    return prompt
