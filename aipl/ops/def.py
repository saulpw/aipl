'''
!!def <opname>
 !op1
 !op2

Create a new op named <opname> that runs the AIPL in the prompt when invoked.
'''

from aipl import defop, Table


@defop('def', None, None)  # immediate
def op_def(aipl, opname, prompt=''):
    'Define composite operator from cmds in prompt (must be indented).'
    cmds = aipl.parse(prompt)

    @defop(opname,
           rankin=cmds[0].op.rankin,
           rankout=cmds[-1].op.rankout)
    def new_operator(aipl, *args, **kwargs):
        arity = 0 if cmds[0].op.rankin is None else 1
        if arity == 0:
            t = aipl.new_input()
        elif arity == 1:
            t = aipl.new_input(args[0])
        ret = aipl.run_cmdlist(cmds, [t], *args[arity:])
        return ret[-1][0].value


def test_def(aipl):
    r = aipl.run_test('''
!!def split-join
 !split
 !join

!split-join
''', 'a b c', 'd e f')
    assert r[0].value == 'a b c'
    assert r[1].value == 'd e f'
