from aipl import defop

@defop('dedup', 1, 1)
def _(aipl, v:list) -> list:
    'Deduplicate a list of scalars.'
    return list(set(v))


def test_dedup(aipl):
    r = aipl.run_test('!split !dedup !sort !join', 'a b a b d c c c a b')
    assert r[0].value == 'a b c d'
