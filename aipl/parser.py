from typing import List, Callable
import textwrap
import sys
from dataclasses import dataclass
import ast
from collections import defaultdict
from lark import Lark, Transformer, Discard, Token

aipl_grammar = Lark(r'''
start: line*

ws: [ _WS ]
_WS: /[ \t]+/

line: commands prompt | _EMPTY_LINE

commands: (command)+
command: command_sign OPNAME arg_list ws

OPNAME: IDENTIFIER

?command_sign: /!!?/

_EMPTY_LINE: "\n"

varname: ">" IDENTIFIER
globalname: ">>" IDENTIFIER
input_col: "<" IDENTIFIER
input_table: "<<" IDENTIFIER

arg_list: arg*

arg: ws (KEY "=" literal | literal | varname | globalname | input_col | input_table)

?literal: BARE_STRING | ESCAPED_STRING
BARE_STRING: /[^ \t\n!"'><]\S*/

ESCAPED_STRING: /(["']).*?(?<!\\)\1/

KEY: IDENTIFIER

IDENTIFIER: /[A-Za-z0-9_-]+/

prompt: ("<< " | "\n") STRING_LINE*
STRING_LINE: /[^!#\n][^\n]*(\n|$)/m | "\n"

COMMENT_LINE: /^#[^\n]*\n/m
%ignore COMMENT_LINE
''', propagate_positions=True)


@dataclass
class Command:
    opname:str
    op: Callable|None
    varnames:List[str]
    globals: List[str]
    input_tables: List[str]
    input_cols: List[str]
    immediate:bool
    args:list
    kwargs:dict
    linenum:int
    prompt:str

    def __str__(self):
        return f'-> {self.opname} (line {self.linenum-1})'  # first line is implicit !!python


class ToAst(Transformer):
    def line(self, tree):
        if len(tree) == 0:
            return tree
        (commands, prompt) = tree
        if prompt:
            commands[-1].prompt = prompt
        return commands

    def commands(self, tree):
        return list(tree)

    def start(self, tree):
        output = []
        for line in tree:
            output.extend(line)
        return output

    def command(self, tree):
        command_sign, opname, arguments = tree

        return Command(
            opname=opname,
            op=None,
            linenum=command_sign.line,
            immediate=command_sign.value == '!!',
            varnames=arguments['varnames'],
            globals=arguments['globalnames'],
            input_cols=arguments['input_cols'],
            input_tables=arguments['input_tables'],
            args=arguments['args'],
            kwargs=dict(arguments['kwargs']),
            prompt=None,
        )

    def OPNAME(self, token):
        return clean_to_id(token.value)

    def command_prompt(self, tree):
        command, prompt = tree
        if prompt:
            command.kwargs['prompt'] = prompt
        return command

    def arg_list(self, arg_list):
        arguments = defaultdict(list)

        for key, arg in arg_list:
            arguments[key].append(arg)

        return arguments

    def varname(self, tree):
        return ('varnames', tree[0])

    def globalname(self, tree):
        return ('globalnames', tree[0])

    def input_table(self, tree):
        return ("input_tables", tree[0])

    def input_col(self, tree):
        return ("input_cols", tree[0])

    def arg(self, tree):
        if isinstance(tree[0], tuple):
            return tree[0]

        if isinstance(tree[0], Token) and tree[0].type == 'KEY':
            return ('kwargs', (clean_to_id(tree[0].value), tree[1]))

        return ('args', tree[0])

    def prompt(self, lines):
        prompt = textwrap.dedent(''.join(token.value for token in lines)).strip()
        if not prompt:
            return None
        return prompt

    def ws(self, tree):
        return Discard

    def BARE_STRING(self, token):
        return trynum(token.value)

    def IDENTIFIER(self, token):
        return token.value

    def ESCAPED_STRING(self, token):
        return ast.literal_eval(token.value)

def parse(program_text):
    parse_tree = aipl_grammar.parse(program_text + "\n")
    return ToAst().transform(parse_tree)


def trynum(x:str) -> int|float|str:
    try:
        return int(x)
    except Exception:
        try:
            return float(x)
        except Exception:
            return x.replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')


def clean_to_id(s:str) -> str:
    return s.replace('-', '_').strip('!')


if __name__ == '__main__':
    for file in sys.argv[1:]:
        print("Parsing: ", file)
        # prepend `!!python` to the input to correctly handle any leading python code
        # see also: AIPL.run() method in interpreter.py
        parse_tree = aipl_grammar.parse('!!python\n' + open(file).read())
        print("Parse tree: ", parse_tree.pretty())
        for command in ToAst().transform(parse_tree):
            print(command)
