import pytest
import textwrap

from .parser import parse

def test_single_line():
    assert ops(parse("!one !two !three\n")) == ["one", "two", "three"]

def test_simple_varname():
    command = parse("!split>output\n")
    assert command[0].opname == "split"
    assert command[0].varnames == ["output"]

def test_split_newlines():
    command = parse("!split sep=\\n\n")
    assert command[0].opname == "split"
    assert command[0].kwargs == {"sep": "\n"}

def test_trailing_empty():
    commands = parse("!split\n\n!ravel\n")

    print(commands)

    assert ops(commands) == ["split", "ravel"]

    assert commands[0].kwargs == {}
    assert commands[1].kwargs == {}

def test_no_final_newline():
    commands = parse("!split")
    assert ops(commands) == ["split"]


def test_no_final_newline_prompt():
    commands = parse("!split\nsome text")
    assert commands[0].opname == "split"
    assert commands[0].kwargs == {"prompt": "some text"}


def test_random_spaces():
    commands = parse("!a !b  \n c  d\n  \n d\n  e\n")
    assert ops(commands) == ["a", "b"]
    assert commands[0].args == []
    assert commands[0].kwargs == {}
    assert commands[1].kwargs == {"prompt": "c  d\n\nd\n e"}


def test_args():
    commands = parse("!fn arg1 arg2 arg3")
    assert commands[0].args == ["arg1", "arg2", "arg3"]


def test_args_with_kwargs():
    commands = parse("!fn arg1 key=abc arg2 key2=def arg3")
    assert commands[0].args == ["arg1", "arg2", "arg3"]
    assert commands[0].kwargs == {"key": "abc", "key2": "def"}


def test_nested_parse():
    commands = parse(textwrap.dedent('''
    !!def split-join
     !split

     !join

    !split-join
    '''))

    assert ops(commands) == ["def", "split_join"]
    assert commands[0].kwargs == {'prompt': "!split\n\n!join"}

def test_quoted():
    commands = parse(r'!fn "arg1" "\"\n"')
    assert commands[0].args == ["arg1", '"\n']

def ops(commands):
    return [command.opname for command in commands]
