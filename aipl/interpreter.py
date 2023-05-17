from typing import List, Dict
from copy import copy
from dataclasses import dataclass
from functools import wraps
import json

from .table import Table, LazyRow, Column, Row
from .db import Database
from .utils import stderr, trynum, fmtargs, fmtkwargs


Scalar = int|float|str

@dataclass
class Command:
    opname:str
    varname:str
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
        self.debug = False
        self.single_step = single_step  # func(Table, Command) to call between steps
        self.globals = {}  # base context

    def parse_cmdline(self, line:str, linenum:int=0) -> List[Command]:
        'Parse single command line into one or more Commands.'
        for cmdstr in line[1:].split(' !'):
            opvar, *rest = cmdstr.split(' ')
            if '>' in opvar:
                opname, varname = opvar.split('>')
            else:
                opname = opvar
                varname = None

            cmd = Command(linenum=linenum+1,
                          line=cmdstr,
                          opname=clean_to_id(opname),
                          varname=varname,
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
                result = self.eval_op(op, inputs, cmd.args, cmd.kwargs, contexts=[self.globals])
                if isinstance(result, Table):
                    inputs = result
                elif op.rankout >= 0:  # otherwise keep former inputs
                    inputs = Table([result])
                if cmd.varname:
                    inputs.axis(1).columns[-1].name = cmd.varname

            except Exception as e:
                stderr(f'\nError (line {cmd.linenum} !{cmd.opname}): {e}')
                raise

        return inputs

    def get_op(self, opname:str):
        return self.operators.get(opname, None)

    def eval_op(self, opfunc, t:Table, args, kwargs, contexts=[], newkey='foo') -> Table:
        # if row.value is a Table, recurse down
        # each row might be different
        if (rank(t) > opfunc.rankin) and (opfunc.arity != 0):
            if isinstance(t, Table):
                ret = copy(t)

            else:
                ret = Table()
            x = dict()
            ret.rows = []
            newkey = self.unique_key
            for row in t:
                try:
                    x = self.eval_op(opfunc, row, args, kwargs, contexts=contexts+[row], newkey=newkey)
                except Exception as e:
                    if self.debug:
                        breakpoint()
                        raise
                    stderr(e)
                    continue
                newrow = copy(row._row)
                if not isinstance(x, dict):
                    newrow[newkey] = x
                else:
                    newrow.update(x)
                ret.rows.append(newrow)
                if isinstance(x, dict):
                    for k in x.keys(): # assumes the last x has the same keys as all rows
                        ret.add_column(Column(k))
                else:
                    ret.add_column(Column(newkey))
            return ret
        elif (opfunc.arity == 0) and (opfunc.rankout == -1):
            r = opfunc(self, *fmtargs(args, contexts), **fmtkwargs(kwargs, contexts))
            return t
        elif (opfunc.arity == 0) and (opfunc.rankout != -1):
            return opfunc(self, *fmtargs(args, contexts), **fmtkwargs(kwargs, contexts))
        else:
            r = opfunc(self, t, *fmtargs(args, contexts), **fmtkwargs(kwargs, contexts))
            if isinstance(r, LazyRow):
                newrow = copy(t._row)
            elif isinstance(r, Table):
                return r
            else:
                newrow = dict()
            if not isinstance(r, dict):
                newrow[newkey] = r
            else:
                newrow.update(r)
            return newrow


        return ret


def prep_input(operand:LazyRow|Table, rankin:int|float) -> Scalar|List[Scalar]|Table|LazyRow:
    if rankin == -1:
        return None
    if rankin == 0:
        assert isinstance(operand, LazyRow)
        return operand.value
    elif rankin == 0.5:
        assert isinstance(operand, LazyRow)
        return operand
    elif rankin == 1:
        if isinstance(operand, LazyRow):
            assert operand.value.rank == 1
            return operand.value.values
        elif isinstance(operand, Table):
            assert operand.rank == 1
            return operand.values
    elif rankin >= 1.5:
        if isinstance(operand, LazyRow):
            #assert operand.value.rank == 1
            return operand.value
        elif isinstance(operand, Table):
            return operand
    else:
        raise Exception("Unexpected rankin")

def prep_output(aipl, in_row:LazyRow, out:Scalar|List[Scalar]|LazyRow|Table, rankout:int|float) -> Scalar|List[Scalar]|Table|LazyRow:
    if rankout == -1:
        return None
    if rankout == 0:
        assert isinstance(out, (int, float, str))
        return out
    elif rankout == 0.5:
        return out
    elif rankout == 1:
        ret = Table()
        assert isinstance(in_row, LazyRow)
        newkey = aipl.unique_key
        ret.rows = [
                {'__parent': in_row, newkey:v}
                    for v in out]
        ret.add_column(Column(newkey))
        return ret
    elif rankout >= 1.5:
        if isinstance(out, Table):
            return out
        else:
            ret = Table()
            ret.rows = list(out)
            for k in ret.rows[0].keys(): # assumes first row has same keys as every other row
                ret.add_column(Column(k))
            return ret

    else:
        raise Exception("Unexpected rankout")




def defop(opname:str, rankin:int|float=0, rankout:int|float=0, arity=1):
    def _decorator(f):

        if arity == 1:
            @wraps(f)
            def _wrapped(aipl, operand:LazyRow|Table, *args, **kwargs) -> LazyRow|Table:
                inp = prep_input(operand, rankin)
                r = f(aipl, inp, *args, **kwargs)
                return prep_output(aipl, operand, r, rankout)
        elif arity == 0:
            @wraps(f)
            def _wrapped(aipl, *args, **kwargs) -> LazyRow|Table:
                r = f(aipl, *args, **kwargs)
                return prep_output(aipl, None, r, rankout)


        _wrapped.rankin = rankin
        _wrapped.rankout = rankout
        _wrapped.arity = arity
        AIPLInterpreter.operators[clean_to_id(opname)] = _wrapped
        return _wrapped
    return _decorator

class Abort(BaseException):
    pass

@defop('abort', -1, -1, arity=0)
def op_abort(aipl):
    raise Abort(f'deliberately aborted')


@defop('debug', -1, -1, arity=0)
def op_debug(aipl, *args):
    aipl.debug = True
    aipl.single_step = lambda *args, **kwargs: breakpoint()

@defop('json', 0.5, 0, 1)
def op_json(aipl, d:LazyRow):
    import json
    return json.dumps(d._asdict())

@defop('parse-json', 0, 0.5, 1)
def op_parse_json(aipl, v:str):
    import json
    return json.loads(v)


@defop('name', 1.5, 1.5)
def op_name(aipl, t:Table, name) -> Table:
    ret = copy(t)
    c = ret.columns[-1]
    c.name = name
    return ret

@defop('ref', 1.5, 1.5)
def op_ref(aipl, t:Table, name):
    'Move column on table to end of columns list (becoming the new .value)'
    col = t.get_column(name)
    if col not in t.columns:
        stderr(f'no such column {name}')
    t.columns.remove(col)
    t.add_column(col)
    return t

@defop('columns', 1.5, 1.5)
def op_columns(aipl, t:Table, *colnames):
    'Set table columns to only those named as args.'
    newcols = []
    for name in colnames:
        c = t.get_column(name)
        if not c:
            colnamestr = ','.join(t.colnames)
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
