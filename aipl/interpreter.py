from typing import List, Dict
from copy import copy
from dataclasses import dataclass
from functools import wraps
import json

from .table import Table, LazyRow, Column
from .db import Database
from .utils import stderr, trynum, fmtargs, fmtkwargs


Scalar = int|float|str

@dataclass
class Command:
    opname:str
    args:list
    kwargs:dict
    line:str
    linenum:int


def clean_to_id(s:str) -> str:
    return s.replace('-', '_')


class AIPLInterpreter(Database):
    operators = {}  # opname:str -> func(aipl, ..., *args, *kwargs)
    next_unique_key = 0

    @property
    def unique_key(self) -> str:
        r = self.next_unique_key
        self.next_unique_key += 1
        return f'_{r}'

    def __init__(self, dbfn='aipl-output.sqlite', single_step=None):
        super().__init__(dbfn)
        self.single_step = single_step  # func(Table, Command) to call between steps

    def parse_cmdline(self, line:str, linenum:int=0) -> List[Command]:
        'Parse single command line into one or more Commands.'
        for cmdstr in line[1:].split(' !'):
            opname, *rest = cmdstr.split(' ')
            cmd = Command(linenum=linenum,
                          line=cmdstr,
                          opname=clean_to_id(opname),
                          args=[],
                          kwargs={})

            for arg in rest:
                if '=' in arg:
                    k, v = arg.split('=', maxsplit=1)
                    cmd.kwargs[clean_to_id(k)] = trynum(v)
                else:
                    cmd.args.append(trynum(arg))

            yield cmd

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

                ret.extend(self.parse_cmdline(line, linenum))

            else:
                prompt += line + '\n'

        if ret:
            prompt = prompt.strip()
            if prompt:
                ret[-1].kwargs['prompt'] = prompt

        return ret

    def run(self, script:str, *args):
        argkey = self.unique_key
        inputs = Table([{argkey:arg} for arg in args])

        for cmd in self.parse(script):
            op = self.get_op(cmd.opname)
            if not op:
                raise Exception(f'no such operator "!{cmd.opname}"')

            stderr(inputs, f'-> {cmd.opname} (line {cmd.linenum})')

            if self.single_step:
                self.single_step(inputs, cmd)

            try:
                result = self.eval_op(op, inputs, cmd.args, cmd.kwargs)
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

    def eval_op(self, opfunc, t:Table|LazyRow|Scalar, args, kwargs, contexts=[]):
        newkey = self.unique_key

        input_rank = rank(t)
        oprank = opfunc.rankin

        if rank(t) <= oprank:  # apply to operand directly
            return opfunc(self, t, *fmtargs(args, contexts), **fmtkwargs(kwargs, contexts))

        elif input_rank > oprank:  # implicit loop over rows in outer table
            newrows = []
            keys_served = {}

            nerrors = 0
            if isinstance(t, LazyRow):
                t = t.value
            for row in t:
                try:
                    r = self.eval_op(opfunc, row, args, kwargs, contexts+[row])
                    if r is not None:
                        row._row[newkey] = r
                        newrows.append(row._row)

                        if opfunc.rankout == 0.5 and input_rank <= oprank+1:
                            for k in r:
                                if k not in keys_served:
                                    keys_served[k] = Column((newkey, k), name=k)

                except Exception as e:
                    stderr(e) # and skip output row
                    nerrors += 1
                    if self.single_step:
                        raise

            if not newrows:
                raise Exception(f'no rows left ({nerrors} errors)')

            ret = copy(t)
            ret.rows = newrows

            if keys_served:
                for k, col in keys_served.items():
                    ret.add_column(col)
            else:
                ret.add_column(Column(newkey))
            return ret


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
        @wraps(f)
        def _wrapped(aipl, t:Table|LazyRow, *args, **kwargs):
            if rankin == 0:  # t is LazyRow but op takes scalar
                r = f(aipl, t.value, *args, **kwargs)
            elif rankin == 0.5:  # op takes LazyRow
                r = f(aipl, t, *args, **kwargs)
            elif rankin == 1:  # t is Table|LazyRow but op takes simple vector
                if isinstance(t, LazyRow):
                    vals = t.value.values
                else:
                    vals = t.values
                r = f(aipl, vals, *args, **kwargs)
            else:  # op takes Table
                if isinstance(t, LazyRow):
                    tbl = t.value
                else:
                    tbl = t
                r = f(aipl, tbl, *args, **kwargs)

            if rankout == 0:
                return r
            elif rankout == 0.5:
                return r
            elif rankout == 1:
                k = aipl.unique_key
                return Table({'__parent':t, k:x} for x in r)
            elif rankout == 1.5:
                if isinstance(r, Table):
                    return r
                k = aipl.unique_key
                return Table({'__parent':t, k:x.value} for x in r)
            elif rankout < 0:
                return t

        _wrapped.rankin = rankin
        _wrapped.rankout = rankout
        _wrapped.arity = arity
        AIPLInterpreter.operators[clean_to_id(opname)] = _wrapped
        return _wrapped
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

@defop('unravel', 1.5, 1.5)
def op_unravel(aipl, v:Table, sep=' '):
    return Table(list(_unravel(v)))

@defop('filter', 0.5, 0.5)
def op_filter(aipl, r:LazyRow):
    if r.value:
        return r

@defop('name', 1.5, 1.5)
def op_name(aipl, t:Table, name):
    c = t.columns[-1]
    c.name = name
    return t

@defop('ref', 1.5, 1.5)
def op_ref(aipl, t:Table, name):
    'Move column on table to end of columns list (becoming the new .value)'
    col = t.get_column(name)
    if col not in t.columns:
        stderr(f'no such column {name}')
    t.columns.remove(col)
    t.add_column(col)
    return t

@defop('select', 1.5, 1.5)
def op_select(aipl, t:Table, *colnames):
    'Set table columns to only those named as args.'
    newcols = []
    for name in colnames:
        c = t.get_column(name)
        if not c:
            colnamestr = ','.join(self.colnames)
            raise Exception(f'no column "{name}" in {colnamestr}')

        newcols.append(c)

    t.columns = newcols
    return t

def rank(v):
    if isinstance(v, LazyRow):
        return rank(v.value)
    if isinstance(v, Table):
        return v.rank
    else:
        return 0
