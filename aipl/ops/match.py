from aipl import defop

@defop('match', 0, 0, 1)
def op_match(aipl, v:str, regex:str) -> bool:
    'Return a bool with whether value matched regex. Used with !filter.'
    import re
    m = re.search(regex, v)
    return m is not None

