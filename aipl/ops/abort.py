from aipl import defop


@defop('abort', None, None, arity=0)
def op_abort(aipl, *args):
    raise UserAbort(*args)
