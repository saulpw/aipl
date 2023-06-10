from aipl import defop, UserAbort


@defop('abort', None, None, arity=0)
def op_abort(aipl, *args):
    "Abort the current chain."
    raise UserAbort(*args)
