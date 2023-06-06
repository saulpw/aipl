from typing import List
import textwrap
import sys
from dataclasses import dataclass

from lark import Lark, Transformer, Discard

aipl_grammar = Lark(r'''
start: line*

ws: [ WS ]
WS: /[ \t]+/

line: command | "\n"
command: (COMMAND | IMMEDIATE_COMMAND) IDENTIFIER varnames arg_list [prompt] ws

COMMAND: "!"
IMMEDIATE_COMMAND: "!!"

varnames: ( ">" IDENTIFIER )*

arg_list: arg*

arg: ws (KEY "=" VALUE | VALUE)

VALUE: /[^ \t\n!>]\S*/
KEY: IDENTIFIER

IDENTIFIER: /[A-Za-z0-9_-]+/

prompt: ws "\n" STRING_LINE*
STRING_LINE: /[^!#\n][^\n]*(\n|$)/ | "\n"

COMMENT_LINE: /^#[^\n]*\n/m

%ignore COMMENT_LINE
''')


@dataclass
class AstCommand:
    opname:str
    varnames:List[str]
    immediate:bool
    args:list
    kwargs:dict
    line:str
    linenum:int

class ToAst(Transformer):
    def line(self, tree):
        return tree

    def start(self, tree):
        return [command[0] for command in tree if command]

    def command(self, tree):
        print("TREE", tree)
        command_sign, opname, varnames, (args, kwargs), prompt = tree

        if prompt is not None:
            kwargs['prompt'] = prompt

        return AstCommand(
            opname=clean_to_id(tree[1].value),
            line=None, # TODO Not yet preserving line contents.
            linenum=command_sign.line,
            immediate=command_sign.type == 'IMMEDIATE_COMMAND',
            varnames=varnames,
            args=args,
            kwargs=kwargs,
        )


    def arg_list(self, arg_list):
        print("Arg list: ", arg_list)
        args = [trynum(arg) for key, arg in arg_list if key is None]
        kwargs = {clean_to_id(key): trynum(value) for key, value in arg_list if key is not None}
        print("Kwargs: ", kwargs)

        return args, kwargs

    def varnames(self, tree):
        return [token.value for token in tree]

    def arg(self, tree):
        if tree[0].type == 'KEY':
            return (tree[0].value, tree[1].value)
        return (None, tree[0].value)

    def prompt(self, lines):
        prompt = textwrap.dedent('\n'.join(token.value for token in lines).strip())
        if not prompt:
            return None
        return prompt

    def ws(self, tree):
        return Discard

def parse(program_text):
    parse_tree = aipl_grammar.parse(program_text)
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
        for command in ToAst().transform(parse_tree):
            print(command)
