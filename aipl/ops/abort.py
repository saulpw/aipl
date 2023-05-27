from aipl import defop


class UserAbort(BaseException):
    pass


@defop('abort', None, None, arity=0)
def op_abort(aipl, *args):
    raise UserAbort(*args)
