from typing import Mapping, List
from collections import ChainMap
import sys


def reprify(s) -> str:
    if isinstance(s, str):
        return s
    return repr(s)

def stderr(*args, **kwargs):
#    args = [strify(x) for x in args]
    args = [reprify(x) for x in args]
    print(*args, file=sys.stderr, flush=True, **kwargs)


def fmtarg(v:str, r:Mapping=None) -> str:
    if isinstance(v, str):
        v = v.encode('utf-8').decode('unicode-escape')
        if r:
            return v.format_map(r)
    return v


def fmtargs(args, contexts:List[Mapping]):
    d = ChainMap(*reversed(contexts))
    return [fmtarg(arg, d) for arg in args]


def fmtkwargs(kwargs, contexts:List[Mapping]):
    d = ChainMap(*contexts)
    return {k:(fmtarg(v, d) if k != 'prompt' else v) for k,v in kwargs.items()}


def trynum(x:str) -> int|float|str:
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
