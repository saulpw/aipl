import pytest

from .interpreter import AIPLInterpreter, defop
from .table import Table


@defop('parse-keyval', 0, 0.5)
def op_parse_keyval(aipl, s:str) -> dict:
    k, v = s.split('=', maxsplit=1)
    return {k:v}

@defop('combine-dict', 1.5, 0.5)
def op_combine_dict(aipl, t:Table) -> dict:
    ret = {}
    for row in t:
        ret.update(row._asdict())
    return ret

@pytest.fixture()
def aipl():
    r = AIPLInterpreter()
#    r.single_step = lambda *args, **kwargs: breakpoint()
    return r


def test_split_join(aipl):
    t = aipl.run('!split !take 3 !join', 'now is the time')
    assert len(t.rows) == 1
    assert t[0] == 'now is the'


def test_op_dicts(aipl):
    'test ops of rankin/rankout == 0.5'
    t = aipl.run('!split sep=, !parse-keyval !combine-dict', 'a=1,b=2,c=3')
    assert t._asdict()[0] == dict(a='1', b='2', c='3')


def test_format(aipl):
    t = aipl.run('!split sep=, !parse-keyval !combine-dict !format\n{first} {last}', 'first=mike,last=smith')
    assert t[0] == 'mike smith'
