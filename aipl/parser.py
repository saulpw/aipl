from typing import List
import textwrap
import sys
from dataclasses import dataclass

from lark import Lark, Transformer

aipl_grammar = Lark(r'''
%ignore " "

start: line*

line: command | "\n"
command: (COMMAND | IMMEDIATE_COMMAND) IDENTIFIER varnames arg* ["\n" prompt]

COMMAND: "!"
IMMEDIATE_COMMAND: "!!"

varnames: ( ">" IDENTIFIER? )*

arg: KEY "=" VALUE | VALUE

VALUE: /[^ \t\n!]\S*/
KEY: IDENTIFIER

IDENTIFIER: /[A-Za-z0-9_-]+/

prompt: STRING_LINE*
STRING_LINE: [ /[^!#][^\n]*/ ] "\n"

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
        command_sign, opname, varnames, *args = tree

        prompt = args.pop()
        kwargs = {k: v for k, v in args if k is not None}
        if prompt is not None:
            kwargs['prompt'] = prompt

        return AstCommand(
            opname=tree[1].value,
            line=None, # TODO Not yet preserving line contents.
            linenum=command_sign.line,
            immediate=command_sign.type == 'IMMEDIATE_COMMAND',
            varnames=varnames,
            args=[v for k, v in args if k is None and v is not None],
            kwargs=kwargs,
        )

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

def parse(program_text):
    parse_tree = aipl_grammar.parse(program_text)
    return ToAst().transform(parse_tree)

if __name__ == '__main__':
    for file in sys.argv[1:]:
        print("Parsing: ", file)
        parse_tree = aipl_grammar.parse(open(file).read())
        for command in ToAst().transform(parse_tree):
            print(command)
