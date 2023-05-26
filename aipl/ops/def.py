'''
!!def <opname>
 !op1
 !op2

Create a new op named <opname> that runs the AIPL in the prompt when invoked.
'''

from aipl import defop, Table


@defop('def', None, None, arity=0)  # immediate
def op_def(aipl, opname, prompt=''):
    'Define composite operator from cmds in prompt (must be indented).'
    cmds = aipl.parse(prompt)

    @defop(opname,
           rankin=cmds[0].op.rankin,
           rankout=cmds[-1].op.rankout,
           arity=cmds[0].op.arity)
    def new_operator(aipl, input, *args, **kwargs):
        argkey = aipl.unique_key
        ret = aipl.run_cmdlist(cmds, Table([{argkey:input}]), *args)
        return ret[0]


def test_def(aipl):
    r = aipl.run('''
!!def split-join
 !split
 !join

!split-join
''', 'a b c', 'd e f')
    assert r[0] == 'a b c'
    assert r[1] == 'd e f'
