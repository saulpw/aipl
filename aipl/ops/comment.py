from aipl import defop


@defop('comment', None, None)
def op_comment(aipl, *args, **kwargs):
    'Do nothing (ignore args and prompt).'
    pass
