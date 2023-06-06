from functools import wraps

from aipl import AIPL, stderr


def dbcache(func):
    'Decorator to persistently cache result from func(aipl, *args, *kwargs).'
    @wraps(func)
    def cachingfunc(aipl:AIPL, *args, **kwargs):
        if not aipl.cache_db:
            return func(aipl, *args, **kwargs)

        key = f'{args} {kwargs}'
        tbl = 'cached_'+func.__name__
        ret = aipl.cache_db.select(tbl, key=key)
        if ret:
            row = ret[-1]
            if 'output' in row:
                return row['output']

            del row['key']
            stderr('[using cached value]')
            return row

        result = func(aipl, *args, **kwargs)

        if isinstance(result, dict):
            aipl.cache_db.insert(tbl, key=key, **result)
        else:
            aipl.cache_db.insert(tbl, key=key, output=result)

        return result

    return cachingfunc


def expensive(mockfunc=None):
    'Decorator to persistently cache result from func(aipl, *args, **kwargs).  Use as @expensive(mock_func) where mock_func has identical signature to func and returns a compatible result during --dry-run.'
    def _decorator(func):
        @wraps(func)
        def _wrapper(aipl:AIPL, *args, **kwargs):
            if aipl.options.dry_run:
                if mockfunc:
                    return mockfunc(aipl, *args, **kwargs)
                else:
                    return f'<{func.__name__}({args} {kwargs})>'

            return dbcache(func)(aipl, *args, **kwargs)

        return _wrapper
    return _decorator
