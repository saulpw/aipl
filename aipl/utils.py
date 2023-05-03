import sys

def stderr(*args, **kwargs):
#    args = [strify(x) for x in args]
    print(*args, file=sys.stderr, **kwargs)


def trynum(x):
    try:
        return int(x)
    except Exception:
        try:
            return float(x)
        except Exception:
            return x


class Bag(dict):
    def __getattr__(self, k):
        return self[k]

    def __setattr__(self, k, v):
        self[k] = v


def strify(x, maxlen=0):
    if isinstance(x, list):
        if not x:
            return '[]'
        return f'[{len(x)}: {strify(x[0], maxlen=15)}]'
    if isinstance(x, dict):
        return '{' + ' '.join(f'{k}={strify(v, maxlen=15)}' for k, v in x.items()) + '}'
    x = str(x).replace("\n", '\\n')
    if maxlen and len(x) > maxlen:
        x = x[:maxlen] + f'...({len(x)} bytes total)'
    return x
