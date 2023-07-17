from typing import List
import textwrap
import sys
from dataclasses import dataclass
import ast
from lark import Lark, Transformer, Discard, Token, Tree

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
inputname: "<" IDENTIFIER
globalname: ">>" IDENTIFIER

arg_list: arg*

arg: ws (KEY "=" literal | literal | varname | globalname | inputname)

?literal: BARE_STRING | ESCAPED_STRING
BARE_STRING: /[^ \t\n!"'><]\S*/

ESCAPED_STRING: /(["']).*?(?<!\\)\1/

KEY: IDENTIFIER

IDENTIFIER: /[A-Za-z0-9_-]+/

prompt: ("< " | "\n") STRING_LINE*
STRING_LINE: /[^!#\n][^\n]*(\n|$)/m | "\n"

COMMENT_LINE: /^#[^\n]*\n/m
%ignore COMMENT_LINE
''', propagate_positions=True)


@dataclass
class AstCommand:
    opname:str
    varnames:List[str]
    globals: List[str]
    inputnames: List[str]
    immediate:bool
    args:list
    kwargs:dict
    line:str
    linenum:int

class ToAst(Transformer):
    def line(self, tree):
        if len(tree) == 0:
            return tree
        (commands, prompt) = tree
        if prompt:
            commands[-1].kwargs['prompt'] = prompt
        return commands

    def commands(self, tree):
        return list(tree)

    def start(self, tree):
        output = []
        for line in tree:
            output.extend(line)
        return output

    def command(self, tree):
        command_sign, opname, (varnames, globalnames, inputnames, args, kwargs) = tree

        return AstCommand(
            opname=opname,
            line=None, # TODO Not yet preserving line contents.
            linenum=command_sign.line,
            immediate=command_sign.value == '!!',
            varnames=varnames,
            globals=globalnames,
            inputnames=inputnames,
            args=args,
            kwargs=kwargs,
        )

    def OPNAME(self, token):
        return clean_to_id(token.value)

    def command_prompt(self, tree):
        command, prompt = tree
        if prompt:
            command.kwargs['prompt'] = prompt
        return command

    def arg_list(self, arg_list):
        args = []
        varnames = []
        globalnames = []
        inputnames = []
        kwargs = {}

        for key, arg in arg_list:
            if key is None:
                args.append(arg)
            elif key == '>':
                varnames.append(arg)
            elif key == '>>':
                globalnames.append(arg)
            elif key == '<':
                inputnames.append(arg)
            else:
                kwargs[clean_to_id(key)] = arg

        return varnames, globalnames, inputnames, args, kwargs


    def varname(self, tree):
        return ('>', tree[0])

    def globalname(self, tree):
        return ('>>', tree[0])

    def inputname(self, tree):
        return ("<", tree[0])

    def arg(self, tree):
        if isinstance(tree[0], tuple):
            return tree[0]

        if isinstance(tree[0], Token) and tree[0].type == 'KEY':
            return (tree[0].value, tree[1])

        return (None, tree[0])

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
        parse_tree = aipl_grammar.parse(open(file).read())
        print("Parse tree: ", parse_tree.pretty())
        for command in ToAst().transform(parse_tree):
            print(command)
