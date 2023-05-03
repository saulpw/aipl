from typing import List, Dict
from dataclasses import dataclass
from functools import wraps

from .table import Table, LazyRow
from .db import Database
from .utils import stderr, Bag, trynum


@dataclass
class Command:
    opname:str
    args:list
    kwargs:Bag
    linenum:int


def clean_to_id(s:str) -> str:
    return s.replace('-', '_')


class AIPLInterpreter(Database):
    operators = {}  # opname:str -> func(aipl, ..., *args, *kwargs)
    next_unique_key = 0

    @property
    def unique_key(self):
        self.next_unique_key += 1
        return self.next_unique_key

#    def __init__(self, dbfn='aipl-output.sqlite'):
#        super().__init__(dbfn)

    def parse_cmdline(self, line:str, linenum:int=0) -> Command:
        'Parse single command line into Command.'
        opname, *rest = line.split(' ')
        cmd = Command(linenum=linenum,
                      opname=clean_to_id(opname[1:]),
                      args=[],
                      kwargs=Bag())

        for arg in rest:
            if '=' in arg:
                k, v = arg.split('=', maxsplit=1)
                cmd.kwargs[clean_to_id(k)] = trynum(v)
            else:
                cmd.args.append(trynum(arg))

        return cmd

    def parse(self, source:str) -> List[Command]:
        'Generate list of Commands from source text'

        prompt = ''
        ret = []

        for linenum, line in enumerate(source.splitlines()):
            if line.startswith('#'):  # comment
                continue

            if line.startswith('!'):  # command
                if ret:
                    prompt = prompt.strip()
                    if prompt:
                        ret[-1].args.append(prompt)

                ret.append(self.parse_cmdline(line, linenum))

            else:
                prompt += line + '\n'

        if ret:
            prompt = prompt.strip()
            if prompt:
                ret[-1].args.append(prompt)

        return ret

    def run(self, script:str, *args):
        inputs = Table([dict(arg=arg) for arg in args])

        for cmd in self.parse(script):
            try:
                func = self.get_op(cmd.opname)
                if not func:
                    raise Exception(f'no such operator "!{cmd.opname}"')

                stderr(inputs, '->', cmd.opname, end='')

                result = inputs.apply(self, func, cmd.args, cmd.kwargs)
                if isinstance(result, Table):
                    inputs = result
                else:
                    inputs = Table([dict(output=result)])

                stderr(' ->', inputs)
            except Exception as e:
                stderr(f'\nError (line {cmd.linenum} !{cmd.opname}): {e}')
                raise

        return inputs

    def get_op(self, opname:str):
        return self.operators.get(opname, None)


def expensive(func):
    'Decorator to persistently cache result from func(r, kwargs).'
    @wraps(func)
    def cachingfunc(db:Database, r:LazyRow, **kwargs):
        key = f'{kwargs} {repr(r)}'
        tbl = 'cached_'+func.__name__

        ret = db.query(f'SELECT * from {tbl} WHERE key=?', key)
        if ret:
            row = ret[-1]
            if 'json' in row:
                return json.loads(row.json)

            return row.output

        result = func(db, df, r, **kwargs)

        if isinstance(result, dict):
            db.insert(tbl, key=key, **result)
        elif isinstance(result, (list, tuple)):
            db.insert(tbl, key=key, json=json.dumps(result))
        else:
            db.insert(tbl, key=key, output=result)

        return result

    return cachingfunc


def defop(opname:str, rankin:int=0, rankout:int=0, arity=1):
    def _decorator(f):
        f.rankin = rankin
        f.rankout = rankout
        f.arity = arity
        AIPLInterpreter.operators[opname] = f
        return f
    return _decorator


@defop('print', 0, 0, 1)
def op_print(aipl, v:str):
    print(v)


@defop('json', 0.5, 0, 1)
def op_json(aipl, d:LazyRow):
    import json
    r = d._asdict()
    return json.dumps(r)


@defop('split', 0, 1, 1)
def op_split(aipl, v:str, sep=' '):
    return v.split(sep)

@defop('join', 1, 0, 1)
def op_join(aipl, v:List[str], sep=' '):
    return sep.join(v)

def _unravel(t:Table):
    for row in t:
        if isinstance(row.value, Table):
            yield from _unravel(row.value)
        else:
            yield dict(value=row.value)

@defop('unravel', 2, 2, 1)
def op_unravel(aipl, v:Table, sep=' '):
    return Table(list(_unravel(v)))

@defop('name', 2, 2, 1)
def op_name(aipl, t:Table, name):
    t.columns[-1].name = name
    return t

@defop('ref', 2, 2, 1)
def op_ref(aipl, t:Table, name):
    col = t.get_column(name)
    t.columns.remove(col)
    t.add_column(col)
    return t

@defop('select', 2, 2, 1)
def op_select(aipl, t:Table, *colnames):
    'Set table columns to only those named as args.'
    t.columns = [t.get_column(name) for name in colnames]
    return t
