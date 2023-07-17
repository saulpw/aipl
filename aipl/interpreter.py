from typing import List, Mapping, Callable
from copy import copy
from dataclasses import dataclass
from functools import wraps
from itertools import cycle

from aipl import Error, AIPLException, InnerPythonException
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
    globals:List[str]
    inputnames:List[str]
    immediate:bool
    args:list
    kwargs:dict
    prompt:str
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
    aliases = {}  # aliasname:str -> builtinopname:str
    next_unique_key:int = 0
    cost_usd:float = 0.0

    def __init__(self, **kwargs):
        self.tables = {}  # named tables
        self.globals = dict(  # base context, imports go into here for later use in the whole script
            aipl=self,
            defop=defop,
            stderr=stderr,
            Table=Table,
        )
        self.options = AttrDict(kwargs)
        self.forced_input = None  # via !test-input
        self.output_db = Database(self.options.outdbfn)
        self.cache_db = None
        if self.options.cachedbfn:
            self.cache_db = Database(self.options.cachedbfn)


    @property
    def unique_key(self) -> str:
        r = self.next_unique_key
        self.next_unique_key += 1
        return f'_{r}'

    def step_breakpoint(self, cmd:Command, *inputs:List[Table]):
        breakpoint()

    def get_op(self, opname:str):
        while opname in self.aliases:
            opname = self.aliases[opname].opname

        return self.operators.get(opname, None)

    def parse(self, source:str) -> List[Command]:
        'Generate list of Commands from source text'

        ast = parser.parse(source)

        commands = []
        for ast_command in ast:
            prompt = ast_command.kwargs.pop('prompt', None)
            command = Command(
                linenum=ast_command.linenum,
                line="", # TODO Capture line contents (or not?)
                opname=ast_command.opname,
                op=self.get_op(ast_command.opname),
                immediate=ast_command.immediate,
                varnames=ast_command.varnames,
                inputnames=ast_command.inputnames,
                globals=ast_command.globals,
                prompt=prompt,
                args=ast_command.args,
                kwargs=ast_command.kwargs
            )

            if not command.op:
                raise AIPLException(
                    f'[line {command.linenum}] no such operator "!{command.opname}"')

            if command.immediate:
                result = self.run_cmdlist([command], [])
                if isinstance(result, Error):
                    if isinstance(result.exception, InnerPythonException):
                        result.exception.command = command
                    raise result.exception

                if command.varnames:
                    last_variable = command.varnames[-1]
                    self.globals[last_variable] = result
                    stderr(f'(global) {last_variable} = result of {command.line}')
            else:
                commands.append(command)
        return commands

    def new_input(self, *inputlines):
        argkey = self.unique_key
        return Table([{argkey:line} for line in inputlines])

    def run_test(self, script:str, *inputlines):
        inputs = [self.new_input(*inputlines)]
        return self.run(script, inputs)[-1]

    def run(self, script:str, inputs:list[Table]=None):
        # lines before first cmdline are Python, to be executed immediately.
        # also add nop at end to do final single-steps.
        cmds = self.parse('!!python\n' + script + '\n!nop')

        return self.run_cmdlist(cmds, inputs)

    def pre_command(self, cmd:Command, t:Table=Table(), *args):
        stderr(t, str(cmd))

    def run_cmdlist(self, cmds:List[Command], inputs:List[Table]):
        for cmd in cmds:
            if self.forced_input is not None:
                inputs.append(self.forced_input)
                self.forced_input = None

            inputargs = [self.tables[arg] for arg in cmd.inputnames]

            operands = [inputs[-1]] if inputs else []
            if cmd.prompt is not None:
                inputargs.append(Table(cmd.prompt))

            if inputargs:
                operands[cmd.op.arity-len(inputargs):] = inputargs

            self.pre_command(cmd, *operands)

            if self.options.step:
                for stepfuncname in self.options.step.split(','):
                    stepfunc = getattr(self, 'step_'+stepfuncname, None)
                    if stepfunc:
                        stepfunc(cmd, *operands)
                    else:
                        stderr(f'no aipl.step_{stepfuncname}!')

            try:
                result = self.eval_op(cmd, *operands, contexts=[self.globals, self.tables])
                if cmd.op.rankout is None:
                    continue # just keep former inputs
                elif isinstance(result, Table):
                    inputs = [result]
                else:
                    k = cmd.varnames[-1] if cmd.varnames else self.unique_key
                    inputs = [Table([{k:result}])]

                for g in cmd.globals:
                    self.tables[g] = inputs[-1]

            except AIPLException as e:
                raise AIPLException(f'AIPL Error (line {cmd.linenum} !{cmd.opname}): {e}') from e
            except Exception as e:
                raise Exception(f'AIPL Error (line {cmd.linenum} !{cmd.opname}): {e}') from e

        for result in inputs:
            if isinstance(result, Error):
                if isinstance(result.exception, InnerPythonException):
                    result.exception.command = command
                raise result.exception

        return inputs

    def call_cmd(self, cmd:Command, contexts:List[Mapping], *inputs, newkey=''):
        operands = [prep_input(arg, rank)
                      for arg,rank in zip(inputs,
                                          [cmd.op.rankin, cmd.op.rankin2])
                   ]
        args = fmtargs(cmd.args, contexts)
        kwargs = fmtkwargs(cmd.kwargs, contexts)

        try:
            if self.options.step and 'break' in self.options.step.split(','):
                breakpoint()

            ret = cmd.op(self, *operands, *args, **kwargs)
        except Exception as e:
            if self.options.debug or self.options.test:
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

    def eval_op(self, cmd:Command, *operands:List[Table|LazyRow], contexts=[], newkey='') -> Table:
        'Recursively evaluate cmd.op(t) with cmd args formatted with contexts'

        if cmd.op.arity == 0:
            return self.call_cmd(cmd, contexts, newkey=newkey)

        else:
            if len(operands) < cmd.op.arity:
                operands = list(operands) + [Table() for i in range(cmd.op.arity-len(operands))]

            t = operands[0]
            if rank(t) <= cmd.op.rankin:
                return self.call_cmd(cmd, contexts, *operands, newkey=newkey)

            if isinstance(t, Table):
                ret = copy(t)
            else:
                ret = copy(t.value)

            # !op>var1>var2 names the deepest column "var2" and the column one-level up (for rankout==1) "var1"
            if cmd.op.rankout is not None and len(cmd.varnames) > cmd.op.rankout and rank(t) == int(cmd.op.rankin+1):
                newkey = cmd.varnames[0] or self.unique_key
            else:
                newkey = newkey or self.unique_key

            for row in t:
                x = self.eval_op(cmd, row, *operands[1:], contexts=contexts+[row], newkey=newkey)

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
        if isinstance(operand, Table) and operand.rank == 0:
            return operand.scalar
        elif isinstance(operand, LazyRow):
            return operand.value
        else:
            assert False, type(operand)
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

def ziplift(a:Table, b:Table):
    'Yield item pairs from `a` and `b`, with the number of elements from the shorter extended (lifted) to match the number of elements from the longer.'

    ita = iter(a)
    itb = iter(b)
    if len(a) > len(b):
        itb = cycle(itb)
    elif len(a) < len(b):
        ita = cycle(ita)
    return zip(ita, itb)

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
            out = list(out)
            ret.rows = [{'__parent': parent_row, varname:v} for parent_row, v in ziplift(in_row, out)]
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
            latest_row = {}  # in case there are no rows in out
            all_keys = set()
            for v in out:
                latest_row = {'__parent': parent_row} if parent_row is not None else {}
                if isinstance(v, dict):
                    all_keys |= set(v.keys())
                    latest_row.update(v)
                else:
                    latest_row[varname] = v
                rows.append(latest_row)

            # use final latest_row to figure out columns
            ret = Table(rows, parent=parent_table)
            if outcols:
                for k in outcols:
                    ret.add_column(Column(k))
            elif all_keys:  # we have to figure out the keys, for better or worse
                for k in all_keys:
                    ret.add_column(Column(k))

            return ret

    else:
        raise Exception("Unexpected rankout")


ranktypes = dict(
    none = None,
    all = 100,
    scalar = 0,
    row = 0.5,
    vector = 1,
    table = 1.5,
)

def defop(opname:str,
          rankin:None|int|float|str=0,
          rankout:None|int|float|str=0,
          *,
          rankin2:None|int|float|str=None,
          outcols:str='',
          preprompt=lambda x: x):
    '''

    '''
    # arity implied by rankin
    if rankin is None:
        arity = 0
    elif rankin2 is None:
        arity = 1
    else:
        arity = 2

    # replace string mnemonic with 'actual' rank
    rankin = ranktypes.get(rankin, rankin)
    rankout = ranktypes.get(rankout, rankout)
    rankin2 = ranktypes.get(rankin2, rankin2)

    def _decorator(f):
        name = clean_to_id(opname)
        f.rankin = rankin
        f.rankout = rankout
        f.rankin2 = rankin2
        f.arity = arity
        f.outcols = outcols
        f.__name__ = name
        f.opname = opname
        f.preprompt = preprompt
        AIPL.operators[name] = f
        return f
    return _decorator


def alias(alias_name:str, builtin_name:str, dialect:str=''):
    'Create an alias `alias_name` for the op `builtin_name`'
    assert alias_name not in AIPL.aliases
    if builtin_name not in AIPL.operators:
        raise AIPLException(f"{builtin_name} is not a valid operator for alias")
    AIPL.aliases[clean_to_id(alias_name)] = AttrDict(opname=builtin_name, dialect=dialect)
