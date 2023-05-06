from typing import List, Dict
from dataclasses import dataclass
from functools import wraps
import json

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

    def __init__(self, dbfn='aipl-output.sqlite', single_step=None):
        super().__init__(dbfn)
        self.single_step = single_step  # func(Table, Command) to call between steps

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
                        ret[-1].kwargs['prompt'] = prompt
                        prompt = ''

                ret.append(self.parse_cmdline(line, linenum))

            else:
                prompt += line + '\n'

        if ret:
            prompt = prompt.strip()
            if prompt:
                ret[-1].kwargs['prompt'] = prompt

        return ret

    def run(self, script:str, *args):
        inputs = Table([dict(arg=arg) for arg in args])

        for cmd in self.parse(script):
            try:
                func = self.get_op(cmd.opname)
                if not func:
                    raise Exception(f'no such operator "!{cmd.opname}"')

                stderr(inputs, '->', cmd.line)

                if self.single_step:
                    self.single_step(inputs, cmd)

                result = inputs.apply(self, func, cmd.args, cmd.kwargs)
                if isinstance(result, Table):
                    inputs = result
                else:
                    inputs = Table([dict(output=result)])

            except Exception as e:
                stderr(f'\nError (line {cmd.linenum} !{cmd.opname}): {e}')
                raise

        return inputs

    def get_op(self, opname:str):
        return self.operators.get(opname, None)


def expensive(func):
    'Decorator to persistently cache result from func(r, kwargs).'
    @wraps(func)
    def cachingfunc(db:Database, *args, **kwargs):
        key = f'{args} {kwargs}'
        tbl = 'cached_'+func.__name__

        ret = db.select(tbl, key=key)
        if ret:
            row = ret[-1]
            if 'output' in row:
                return row['output']

            del row['key']
            return row

        result = func(db, *args, **kwargs)

        if isinstance(result, dict):
            db.insert(tbl, key=key, **result)
        else:
            db.insert(tbl, key=key, output=result)

        return result

    return cachingfunc


def defop(opname:str, rankin:int=0, rankout:int=0, arity=1):
    def _decorator(f):
        f.rankin = rankin
        f.rankout = rankout
        f.arity = arity
        AIPLInterpreter.operators[clean_to_id(opname)] = f
        return f
    return _decorator


@defop('json', 0.5, 0, 1)
def op_json(aipl, d:LazyRow):
    import json
    return json.dumps(d._asdict())

def _unravel(t:Table):
    for row in t:
        if isinstance(row.value, Table):
            yield from _unravel(row.value)
        else:
            yield dict(value=row.value)

@defop('unravel', 2, 2, 1)
def op_unravel(aipl, v:Table, sep=' '):
    return Table(list(_unravel(v)))

@defop('filter', 2, 2, 1)
def op_filter(aipl, t:Table):
    for row in t:
        if row.value:
            yield row

@defop('name', 2, 2, 1)
def op_name(aipl, t:Table, name):
    c = t.columns[-1]
    c.name = name
    return t

@defop('ref', 2, 2, 1)
def op_ref(aipl, t:Table, name):
    'Move column on table to end of columns list (becoming the new .value)'
    col = t.get_column(name)
    t.columns.remove(col)
    t.add_column(col)
    return t

@defop('select', 2, 2, 1)
def op_select(aipl, t:Table, *colnames):
    'Set table columns to only those named as args.'
    newcols = []
    for name in colnames:
        c = t.get_column(name)
        if not c:
            colnamestr = ','.join(self.colnames)
            raise Exception(f'no column "{name}" in {colnamestr}')

        newcols.add_column(c)

    t.columns = newcols
    return t
