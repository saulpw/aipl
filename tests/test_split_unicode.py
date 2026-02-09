import pytest
from aipl.interpreter import AIPL

def test_split_unicode(aipl):
    t = aipl.run_test("!split sep='\u2022'", 'now•is•the•time')
    assert len(t.rows) == 4
