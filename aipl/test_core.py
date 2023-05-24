from typing import List

import pytest

from .interpreter import AIPLInterpreter, defop
from .table import Table, LazyRow


@defop('parse-keyval', 0, 0.5)
def op_parse_keyval(aipl, s:str) -> dict:
    k, v = s.split('=', maxsplit=1)
    return {k:v}

@defop('parse-keyvals', 0, 1.5)
def op_parse_keyvals(aipl, s:str) -> List[dict]:
    for arg in s.split(','):
        k, v = arg.split('=', maxsplit=1)
        yield {k:v}

@defop('combine-dict', 1.5, 0.5)
def op_combine_dict(aipl, t:Table) -> dict:
    ret = {}
    for row in t:
        ret.update(row._asdict())
    return ret

@defop('cases', 0, 0.5)
def op_cases(aipl, v:str) -> dict:
    return dict(upper=v.upper(), lower=v.lower())

@defop('lowercase', 0, 0)
def op_lowercase(aipl, v:str) -> str:
    return v.lower()

@defop('uppercase', 0, 0)
def op_uppercase(aipl, v:str) -> str:
    return v.upper()


def test_lowercase(aipl):
    # scalar to scalar
    # 2 rows; single column
    t = aipl.run('!split !lowercase !join', 'A b C', 'DeF')
    assert len(t.rows) == 2
    assert t[0] == 'a b c'
    assert t[1] == 'def'

def test_cases(aipl):
    t = aipl.run('!split !cases !join', 'A b C', 'DeF')
    assert len(t.rows) == 2
    assert t[0] == 'a b c'
    assert t[1] == 'def'

def test_toplevel_join(aipl):
    t = aipl.run('!join', 'now', 'is', 'the')
    assert len(t.rows) == 1
    assert t[0] == 'now is the'

def test_split_join(aipl):
    t = aipl.run('!split !take 3 !join', 'now is the time')
    assert len(t.rows) == 1
    assert t[0] == 'now is the'


def xtest_op_dicts(aipl):
    'test ops of rankin/rankout == 0.5'
    t = aipl.run('!split sep=, !parse-keyval !combine-dict', 'a=1,b=2,c=3')
    assert t._asdict()[0] == dict(a='1', b='2', c='3')


def xtest_op_multiple_dicts(aipl):
    'test ops of rankin/rankout == 0.5'
    t = aipl.run('!parse-keyvals !combine-dict', 'a=1,b=2,c=3')
    assert t._asdict()[0] == dict(a='1', b='2', c='3')


def xtest_format(aipl):
    t = aipl.run('!split sep=, !parse-keyval !combine-dict !format\n{first} {last}', 'last=smith,first=mike')
    assert t[0] == 'mike smith'


def test_match_filter(aipl):
    t = aipl.run('!split !name keep !match ^z !filter !join', 'ab zh cd zq azzz z')
    assert t[0] == 'zh zq z'


def test_unravel(aipl):
    t = aipl.run('!split !take 2 !unravel !join', 'a b c d', 'e f g')
    assert t[0] == 'a b e f'
