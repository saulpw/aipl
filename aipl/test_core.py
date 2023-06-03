from typing import List
from collections import defaultdict
import string

import pytest

from .interpreter import defop
from .table import Table, LazyRow


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

@defop('cases', 0, 0.5)
def op_cases(aipl, v:str) -> dict:
    return dict(upper=v.upper(), lower=v.lower())

@defop('lowercase', 0, 0)
def op_lowercase(aipl, v:str) -> str:
    return v.lower()

@defop('uppercase', 0, 0)
def op_uppercase(aipl, v:str) -> str:
    return v.upper()

@defop('lettertypes', 0, 1.5, outcols='letters digits')
def op_letters(aipl, v:str) -> List[dict]:
    'Yield dict(letters=, digits=) for each word in input.'
    for word in v.split():
        letters = defaultdict(int)
        for c in word:
            if c in string.ascii_letters:
                letters['letters'] += 1
            elif c in string.digits:
                letters['digits'] += 1
        yield letters

def test_lowercase(aipl):
    # scalar to scalar
    # 2 rows; single column
    t = aipl.run('!split !lowercase !join', 'A b C', 'DeF')
    assert len(t.rows) == 2
    assert t[0].value == 'a b c'
    assert t[1].value == 'def'

def test_cases(aipl):
    t = aipl.run('!split !cases !join', 'A b C', 'DeF')
    assert len(t.rows) == 2
    assert t[0].value == 'a b c'
    assert t[1].value == 'def'


def test_op_dicts(aipl):
    'test ops of rankin/rankout == 0.5'
    t = aipl.run('!split sep=, !parse-keyval !combine-dict', 'a=1,b=2,c=3')
    assert t._asdict()[0] == dict(a='1', b='2', c='3')


def test_col_reference(aipl):
    t = aipl.run('!split sep=, !parse-keyval !combine-dict !format\n{first} {last}', 'last=smith,first=mike')
    assert t[0].value == 'mike smith'


def test_out_table_dict(aipl):
    'Tests when a rankout of 1.5 is returned a dict.'
    r = aipl.run('!lettertypes', '1abc cd23 de53')
    t = r[0].value
    assert set(t.colnames) == set(['digits', 'letters'])
    assert t[0]['digits'] == 1 and t[0]['letters'] == 3
