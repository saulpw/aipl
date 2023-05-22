from typing import List, Dict, Mapping, Callable
from copy import copy
from dataclasses import dataclass
from functools import wraps
import math
import json
import re

from .table import Table, LazyRow, Column, Row, ParentColumn
from .db import Database
from .utils import stderr, trynum, fmtargs, fmtkwargs
from .utils import stderr, trynum, fmtargs, fmtkwargs


Scalar = int|float|str

@dataclass
class Command:
    opname:str
    op:Callable
    varnames:List[str]
    args:list
    kwargs:dict
    line:str
    linenum:int


class AIPLException(Exception):
    pass


def clean_to_id(s:str) -> str:
    return s.replace('-', '_')


def rank(v):
    if isinstance(v, LazyRow):
        return rank(v.value)
    if isinstance(v, Table):
        return v.rank
    else:
        return 0


class AIPLInterpreter(Database):
    operators = {}  # opname:str -> func(aipl, ..., *args, *kwargs)
    next_unique_key = 0

    @property
    def unique_key(self) -> str:
        r = self.next_unique_key
        self.next_unique_key += 1
        return f'_{r}'

    def __init__(self, dbfn='aipl-output.sqlite', single_step=None, debug=True):
        super().__init__(dbfn)
        self.debug = debug
        self.single_step = single_step  # func(Table, Command) to call between steps
        self.globals = {}  # base context

    def parse_cmdline(self, line:str, linenum:int=0) -> List[Command]:
        'Parse single command line into one or more Commands.'
        for cmdstr in line[1:].split(' !'):
            opvar, *rest = cmdstr.split(' ')
            if '>' in opvar:
                opname, *varnames = opvar.split('>')
            else:
                opname = opvar
                varnames = []

            opname = clean_to_id(opname)
            cmd = Command(linenum=linenum+1,
                          line=cmdstr,
                          opname=opname,
                          op=self.get_op(opname),
                          varnames=varnames,
                          args=[],
                          kwargs={})

            if not cmd.op:
                stderr(f'[line {cmd.linenum}] no such operator "!{cmd.opname}"')
                self.operators['abort'](self)

            for arg in rest:
                m = re.match(r'(\w+)=(.*)', arg)
                if m:
                    k, v = m.groups()  # arg.split('=', maxsplit=1)
                    cmd.kwargs[clean_to_id(k)] = trynum(v)
                else:
                    cmd.args.append(trynum(arg))

            yield cmd

    def get_op(self, opname:str):
        return self.operators.get(opname, None)

    def parse(self, source:str) -> List[Command]:
        'Generate list of Commands from source text'

        prompt = ''
        ret = []

        def set_last_prompt(ret, prompt):
            import textwrap
            if ret:
                prompt = prompt.strip('\n')
                if prompt:
                    ret[-1].kwargs['prompt'] = textwrap.dedent(prompt)

        for linenum, line in enumerate(source.splitlines()):
            if line.startswith('#'):  # comment
                continue

            if line.startswith('!'):  # command
                set_last_prompt(ret, prompt)
                prompt = ''

                ret.extend(self.parse_cmdline(line, linenum))

            else:
                prompt += line + '\n'

        set_last_prompt(ret, prompt)

        return ret

    def run(self, script:str, *args):
        argkey = self.unique_key
        inputs = Table([{argkey:arg} for arg in args])

        for cmd in self.parse(script):
            stderr(inputs, f'-> {cmd.opname} (line {cmd.linenum})')

            if self.single_step:
                self.single_step(inputs, cmd)

            try:
                result = self.eval_op(cmd, inputs, contexts=[self.globals])
                if isinstance(result, Table):
                    inputs = result
                elif cmd.op.rankout is not None:  # otherwise keep former inputs
                    inputs = Table([{self.unique_key: result}], parent=inputs)

            except Exception as e:
                stderr(f'\nError (line {cmd.linenum} !{cmd.opname}): {e}')
                raise

        return inputs

    def call_cmd(self, cmd:Command, contexts:List[Mapping], *inputs):
        try:
            ret = cmd.op(self, *inputs, *fmtargs(cmd.args, contexts), **fmtkwargs(cmd.kwargs, contexts))
        except Exception as e:
            if self.debug:
                raise
            stderr(e)
            return None

        if cmd.op.rankout is not None and len(cmd.varnames) > cmd.op.rankout:
            varname = cmd.varnames[int(cmd.op.rankout)] or self.unique_key
        else:
            varname = self.unique_key

        return prep_output(self, inputs[0] if inputs else None, ret, cmd.op.rankout, varname)

    def eval_op(self, cmd:Command, t:Table, contexts=[], newkey='') -> Table:
        'Recursively evaluate cmd.op(t) with cmd args formatted with contexts'

        if cmd.op.arity == 0:
            ret = self.call_cmd(cmd, contexts)
            if cmd.op.rankout is None:
                assert not ret  # ignore return value (no rankout)
                return t

        elif rank(t) <= cmd.op.rankin:
            ret = self.call_cmd(cmd, contexts, t)

        else:
            if isinstance(t, Table):
                ret = Table(parent=t)
            else:
                ret = Table(parent=t.value)

            if cmd.varnames and rank(t) == int(cmd.op.rankin+1):
                newkey = cmd.varnames[0] or self.unique_key
            else:
                newkey = newkey or self.unique_key

            for row in t:
                x = self.eval_op(cmd, row, contexts=contexts+[row], newkey=newkey)

                if x is None:
                    continue

                newrow = {}
                newrow['__parent'] = row
                ret.rows.append(update_dict(newrow, x, newkey))

            if isinstance(x, dict):
                for k in x.keys():  # assumes the last x has the same keys as all rows
                    vname = (newkey+'_'+k) if len(x) > 1 else newkey
                    ret.add_column(Column(k, vname))
            else:
                ret.add_column(Column(newkey))

        return ret


def update_dict(d:dict, elem, key:str='') -> dict:
    'Update d with elem if elem is dict, otherwise add d[key]=elem.  Return d.'
    if isinstance(elem, dict):
        d.update(elem)
    else:
        d[key] = elem
    return d


def prep_input(operand:LazyRow|Table, rankin:int|float) -> Scalar|List[Scalar]|Table|LazyRow:
    if rankin is None:
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


def prep_output(aipl,
                in_row:LazyRow,
                out:Scalar|List[Scalar]|LazyRow|Table,
                rankout:int|float,
                varname:str) -> Scalar|List[Scalar]|Table|LazyRow:

    if rankout is None:
        return None

    if rankout == 0:
        assert not isinstance(out, (Table, LazyRow, dict))
        return out

    elif rankout == 0.5:
        return out

    elif rankout == 1:
        assert isinstance(in_row, LazyRow)
        ret = Table()
        ret.rows = [{'__parent': in_row, varname:v} for v in out]
        ret.add_column(Column(varname))
        return ret

    elif rankout >= 1.5:
        if isinstance(out, Table):
            return out
        else:
            ret = Table(parent=in_row._table)
            ret.rows = [{'__parent': in_row, varname:v} for v in out]
            for k in ret.rows[0].keys():  # assumes first row has same keys as every other row
                ret.add_column(Column(k))
            return ret

    else:
        raise Exception("Unexpected rankout")



def defop(opname:str, rankin:int|float=0, rankout:int|float=0, arity=1):
    def _decorator(f):
        @wraps(f)
        def _wrapped(aipl, *args, **kwargs) -> LazyRow|Table:
            operands = [prep_input(operand, rankin) for operand in args[:arity]]
            return f(aipl, *operands, *args[arity:], **kwargs)

        _wrapped.rankin = rankin
        _wrapped.rankout = rankout
        _wrapped.arity = arity
        AIPLInterpreter.operators[clean_to_id(opname)] = _wrapped
        return _wrapped
    return _decorator
