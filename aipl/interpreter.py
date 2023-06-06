from typing import List, Mapping, Callable
from copy import copy
from dataclasses import dataclass
from functools import wraps

from aipl import Error, AIPLException
from .table import Table, LazyRow, Column
from .db import Database
from .utils import stderr, fmtargs, fmtkwargs, AttrDict
from .parser import clean_to_id
from . import parser


Scalar = int|float|str

@dataclass
class Command:
    opname:str
    op:Callable
    varnames:List[str]
    immediate:bool
    args:list
    kwargs:dict
    line:str
    linenum:int

    def __str__(self):
        return f'-> {self.opname} (line {self.linenum})'


class UserAbort(BaseException):
    'UserAbort not caught by internal error handling; will always exit.'


def rank(v):
    if isinstance(v, LazyRow):
        return rank(v.value)
    if isinstance(v, Table):
        return v.rank
    else:
        return 0


class AIPL:
    operators = {}  # opname:str -> func(aipl, ..., *args, *kwargs)
    next_unique_key:int = 0
    cost_usd:float = 0.0

    def __init__(self, **kwargs):
        self.globals = {}  # base context
        self.options = AttrDict(kwargs)
        self.output_db = Database(self.options.outdbfn)

        self.cache_db = None
        if self.options.cachedbfn:
            self.cache_db = Database(self.options.cachedbfn)


    @property
    def unique_key(self) -> str:
        r = self.next_unique_key
        self.next_unique_key += 1
        return f'_{r}'

    def step_breakpoint(self, t:Table, cmd:Command):
        breakpoint()

    def get_op(self, opname:str):
        return self.operators.get(opname, None)

    def parse(self, source:str) -> List[Command]:
        'Generate list of Commands from source text'

        ast = parser.parse(source)

        commands = []
        for ast_command in ast:
            command = Command(
                linenum=ast_command.linenum,
                line="", # TODO Capture line contents (or not?)
                opname=ast_command.opname,
                op=self.get_op(ast_command.opname),
                immediate=ast_command.immediate,
                varnames=ast_command.varnames,
                args=ast_command.args,
                kwargs=ast_command.kwargs
            )

            if not command.op:
                raise AIPLException(
                    f'[line {command.linenum}] no such operator "!{command.opname}"',
                    command)

            if (command.immediate):
                result = self.eval_op(command, Table(), contexts=[self.globals])
                if command.varnames:
                    last_variable = command.varnames[-1]
                    self.globals[last_variable] = result
                    stderr(f'(global) {last_variable} = result of {command.line}')
            else:
                commands.append(command)
        return commands

    def run(self, script:str, *args):
        cmds = self.parse(script)

        argkey = self.unique_key
        inputs = Table([{argkey:arg} for arg in args])
        return self.run_cmdlist(cmds, inputs)

    def pre_command(self, t:Table, cmd:Command):
        stderr(t, str(cmd))

    def run_cmdlist(self, cmds:List[Command], inputs):
        for cmd in cmds:
            self.pre_command(inputs, cmd)

            if self.options.step:
                for stepfuncname in self.options.step.split(','):
                    stepfunc = getattr(self, 'step_'+stepfuncname, None)
                    if stepfunc:
                        stepfunc(inputs, cmd)
                    else:
                        stderr(f'no aipl.step_{stepfuncname}!')

            try:
                result = self.eval_op(cmd, inputs, contexts=[self.globals])
                if cmd.op.rankout is None:
                    continue # just keep former inputs
                elif isinstance(result, Table):
                    inputs = result
                else:
                    k = cmd.varnames[-1] if cmd.varnames else self.unique_key
                    inputs = Table([{k:result}])

            except AIPLException as e:
                raise AIPLException(f'AIPL Error (line {cmd.linenum} !{cmd.opname}): {e}') from e
            except Exception as e:
                raise Exception(f'AIPL Error (line {cmd.linenum} !{cmd.opname}): {e}') from e

        return inputs

    def call_cmd(self, cmd:Command, contexts:List[Mapping], *inputs, newkey=''):
        try:
            ret = cmd.op(self, *inputs, *fmtargs(cmd.args, contexts), **fmtkwargs(cmd.kwargs, contexts))
        except Exception as e:
            if self.options.debug:
                raise
            return Error(cmd.linenum, cmd.opname, e)

        if cmd.op.rankout is not None and cmd.varnames:
            varname = cmd.varnames[-1]
        else:
            varname = newkey or self.unique_key

        return prep_output(self,
                           inputs[0] if inputs else None,
                           ret,
                           cmd.op.rankout,
                           cmd.op.outcols.split(),
                           varname)

    def eval_op(self, cmd:Command, t:Table|LazyRow, contexts=[], newkey='') -> Table:
        'Recursively evaluate cmd.op(t) with cmd args formatted with contexts'

        if cmd.op.arity == 0:
            ret = self.call_cmd(cmd, contexts, newkey=newkey)
            if cmd.op.rankout is None:
                assert not ret  # ignore return value (no rankout)
                return t

        elif rank(t) <= cmd.op.rankin:
            ret = self.call_cmd(cmd, contexts, t, newkey=newkey)

        else:
            if isinstance(t, Table):
                ret = Table()
                for c in t.columns:
                    ret.add_column(copy(c))
            else:
                ret = Table()
                for c in t.value.columns:
                    ret.add_column(copy(c))

            # !op>var1>var2 names the deepest column "var2" and the column one-level up (for rankout==1) "var1"
            if cmd.op.rankout is not None and len(cmd.varnames) > cmd.op.rankout and rank(t) == int(cmd.op.rankin+1):
                newkey = cmd.varnames[0] or self.unique_key
            else:
                newkey = newkey or self.unique_key

            x = dict()
            for row in t:
                x = self.eval_op(cmd, row, contexts=contexts+[row], newkey=newkey)

                if x is None:
                    continue

                ret.rows.append(update_dict(row._row, x, newkey))

                if isinstance(x, Mapping):
                    for k in x.keys():
                        ret.add_column(Column(k, k))
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


def prep_input(operand:LazyRow|Table|Error, rankin:int|float) -> Scalar|List[Scalar]|Table|LazyRow:
    if isinstance(operand, Error):
        return operand

    if rankin is None:
        return None
    if rankin == 0:
        assert isinstance(operand, LazyRow), type(operand)
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
                in_row:LazyRow|Table,
                out:Scalar|List[Scalar]|LazyRow|Table,
                rankout:int|float,
                outcols:List[str],
                varname:str) -> Scalar|List[Scalar]|Table|LazyRow:

    if rankout is None:
        return None

    if rankout == 0:
        assert not isinstance(out, (Table, LazyRow, dict))
        return out

    elif rankout == 0.5:
        return out

    elif rankout == 1:
        ret = Table()
        if isinstance(in_row, LazyRow):
            ret.rows = [{'__parent': in_row, varname:v} for v in out]
        elif isinstance(in_row, Table):
            ret.rows = [{'__parent': parent_row, varname:v} for parent_row, v in zip(in_row, out)]
        else:
            assert False, 'unknown type for in_row'
        ret.add_column(Column(varname))
        return ret

    elif rankout >= 1.5:
        if isinstance(out, Table):
            return out
        else:
            if in_row is None:
                parent_table = None
                parent_row = None
            elif isinstance(in_row, Table):
                parent_table = None
                parent_row = None
            elif isinstance(in_row, LazyRow):
                parent_table = in_row._table
                parent_row = in_row
            else:
                raise Exception(f'unknown type for in_row: {type(in_row)}')

            rows = []
            d = {}  # in case there are no rows in out
            for v in out:
                d = {'__parent': parent_row} if parent_row is not None else {}
                if isinstance(v, dict):
                    d.update(v)
                else:
                    d[varname] = v
                rows.append(d)

            ret = Table(rows, parent=parent_table)
            if outcols:
                for k in outcols:
                    ret.add_column(Column(k))
            elif d:  # we figure it out and it's gay
                for k in d:
                    ret.add_column(Column(k))

            return ret

    else:
        raise Exception("Unexpected rankout")


def defop(opname:str, rankin:None|int|float=0, rankout:int|float=0, arity=1, outcols:str='', preprompt=lambda x: x):
    if rankin is None:
        arity = 0  # no explict arity for nonary or unary ops

    def _decorator(f):
        @wraps(f)
        def _wrapped(aipl, *args, **kwargs) -> LazyRow|Table:
            operands = [prep_input(operand, rankin) for operand in args[:arity]]
            return f(aipl, *operands, *args[arity:], **kwargs)

        name = clean_to_id(opname)
        _wrapped.rankin = rankin
        _wrapped.rankout = rankout
        _wrapped.arity = arity
        _wrapped.outcols = outcols
        _wrapped.__name__ = name
        _wrapped.preprompt = lambda prompt: preprompt(prompt)
        AIPL.operators[name] = _wrapped
        return _wrapped
    return _decorator
