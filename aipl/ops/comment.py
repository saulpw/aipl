from aipl import defop


@defop('comment', None, None, arity=0)
def op_comment(aipl, *args, **kwargs):
    'Do nothing (ignoring args and prompt).'
    pass
