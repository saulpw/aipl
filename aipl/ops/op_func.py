from copy import copy
from typing import List, Dict
from collections import defaultdict

from aipl import defop
from aipl.table import Table, LazyRow, Column, ParentColumn


@defop('def', None, None, arity=0)  # immediate
def op_def(aipl, opname, prompt=''):
    cmds = aipl.parse(prompt)

    @defop(opname,
           rankin=cmds[0].op.rankin,
           rankout=cmds[-1].op.rankout,
           arity=cmds[0].op.arity)
    def new_operator(aipl, input, *args, **kwargs):
        argkey = aipl.unique_key
        ret = aipl.run_cmdlist(cmds, Table([{argkey:input}]), *args)
        return ret[0]
