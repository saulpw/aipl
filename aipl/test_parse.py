import pytest
import textwrap

from .parser import parse

def test_single_line():
    assert ops(parse("!one !two !three\n")) == ["one", "two", "three"]

def test_simple_varname():
    command = parse("!split>output\n")
    assert command[0].opname == "split"
    assert command[0].kwargs == {}
    assert command[0].args == []
    assert command[0].varnames == ["output"]

def test_varname_afterwards():
    command = parse("!op arg >var")
    assert command[0].opname == "op"
    assert command[0].args == ["arg"]
    assert command[0].varnames == ["var"]

def test_global():
    command = parse("!op arg >>global_name")
    assert command[0].opname == "op"
    assert command[0].args == ["arg"]
    assert command[0].varnames == []
    assert command[0].globals == ["global_name"]

def test_split_newlines():
    command = parse("!split sep=\\n\n")
    assert command[0].opname == "split"
    assert command[0].kwargs == {"sep": "\n"}

def test_trailing_empty():
    commands = parse("!split\n\n!ravel\n")

    assert ops(commands) == ["split", "ravel"]

    assert commands[0].kwargs == {}
    assert commands[1].kwargs == {}

def test_no_final_newline():
    commands = parse("!split")
    assert ops(commands) == ["split"]


def test_no_final_newline_prompt():
    commands = parse("!split\nsome text")
    assert commands[0].opname == "split"
    assert commands[0].prompt == "some text"


def test_random_spaces():
    commands = parse("!a !b  \n c  d\n  \n d\n  e\n")
    assert ops(commands) == ["a", "b"]
    assert commands[0].args == []
    assert commands[0].kwargs == {}
    assert commands[1].prompt == "c  d\n\nd\n e"


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
    assert commands[0].prompt == "!split\n\n!join"

def test_quoted():
    commands = parse(r'!fn "arg1" "\"\n"')
    assert commands[0].args == ["arg1", '"\n']

def test_single_quoted():
    commands = parse(r"!fn 'arg1' '\'\n'")
    assert commands[0].args == ["arg1", "'\n"]

def test_numbers():
    commands = parse("!fn 1 2.0 3.0e10 -3 -2e-7")
    assert commands[0].args == [1, 2.0, 3.0e10, -3, -2e-7]

def test_input_cols():
    commands = parse("!split <b sep=: <a")
    assert commands[0].opname == "split"
    assert commands[0].args == []
    assert commands[0].kwargs == {"sep": ":"}
    assert commands[0].input_cols == ["b", "a"]

def test_input_globals():
    commands = parse("!split <<b sep=: <<a")
    assert commands[0].opname == "split"
    assert commands[0].args == []
    assert commands[0].kwargs == {"sep": ":"}
    assert commands[0].input_tables == ["b", "a"]

def test_inline_prompt():
    commands = parse("!split sep=: << a:b:c")
    assert commands[0].opname == "split"
    assert commands[0].args == []
    assert commands[0].kwargs == {"sep": ":"}
    assert commands[0].prompt == "a:b:c"

def test_multiple_commands():
    commands = parse("!a !b !c << a:b:c")
    assert commands[0].opname == "a"
    assert commands[1].opname == "b"
    assert commands[2].opname == "c"
    assert commands[2].args == []
    assert commands[2].kwargs == {}
    assert commands[2].prompt == "a:b:c"

def test_inline_prompt_with_newline():
    commands = parse("!split sep=: << a:b:c\nd:e:f\ng: :h\n")
    assert commands[0].opname == "split"
    assert commands[0].args == []
    assert commands[0].kwargs == {"sep": ":"}
    assert commands[0].prompt == "a:b:c\nd:e:f\ng: :h"


def ops(commands):
    return [command.opname for command in commands]
