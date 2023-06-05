import pytest

from .parser import parse, AstCommand

def test_single_line():
    assert ops(parse("!one !two !three\n")) == ["one", "two", "three"]

def ops(commands):
    return [command.opname for command in commands]
