# Writing a New Operator in Python

In AIPL you can use !!python to add a new operator.  For instance, here's the definition of `!lower`, a scalar string to string operator:

    !!python
    @defop('lower', rankin=0, rankout=0)
    def _(aipl, v:str) -> str:
        return v.lower()

## Operators internal to the AIPL codebase

All .py files in aipl.ops are imported automatically.
You can use the exact same code from the prompt above.

Each and every operator internal to the aipl codebase should have:

  - Full docs for operator in the file's docstring, including any subtleties or warts
  - Concise docs in function's docstring.
  - At least one basic test and demonstration of functionality

Any imports of external libraries should be done within the operator itself, not at toplevel.

## Full Example: `aipl/ops/lower.py`

    '''
    !lower converts the input string to lowercase.
    Unicode cased characters are supported per [Python str.lower]().
    '''

    from aipl import defop


    @defop('lower', rankin='scalar', rankout='scalar')
    def _(aipl, v:str) -> str:
        'Convert the input string to lowercase.'
        return v.lower()


    def test_lower(aipl):
        r = aipl.run('!lower', 'HEY you')
        assert r[0] == 'hey you'
