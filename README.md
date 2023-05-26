# AIPL (Array-Inspired Pipeline Language)

[![Tests](https://github.com/saulpw/aipl/workflows/aipl-testing/badge.svg)](https://github.com/saulpw/aipl/actions/workflows/main.yml)
[![discord](https://img.shields.io/discord/880915750007750737?label=discord)](https://visidata.org/chat)

A tiny DSL to make it easier to explore and experiment with AI pipelines.

## Features

- array language semantics (implicit looping over input)
- tacit dataflow (output from previous command becomes input to next command)
- entire pipeline defined in same file and in execution order for better understanding
  - including inline prompt templates
- persistent cache of expensive operations into a sqlite db

## Why?

The recent developments in LLMs and AI are a whole new level of capabilities (and costs).
I wanted to see what all the fuss was about, so I tried to do some basic things with [langchain](https://github.com/hwchase17/langchain) but it was this big complicated system.
So instead I implemented some small workflows myself with raw Python, and it turned out that AI is actually pretty straightforward.
This is just a small hackable platform that makes it easy to experiment and get small-scale results.
For now it's called AIPL.

## Design

AIPL is intended as a simple platform for quick proof of concept data pipelines to be implemented and tested.

### Emphasize the Dataflow

An AIPL script represents the essence of a data pipeline, with only the high-level operations and their parameters and prompts.
No boilerplate or quoting or complicated syntax.
Not even much of a language--just commands executed in order.
This keeps the focus on data flow and the high-level operations--the actual links in the chain.
It can be expanded or optimized or parallelized as needed.

### Very Little Overhead

AIPL is array-oriented and concatenative, drawing inspiration from APL and Forth, both of which have powerful operators and very simple syntax.
Passing data implicitly between operators allows for efficient representation of data flows, and avoids [one of the hardest problems in computer science](https://www.namingthings.co/).
And the implicit looping of array languages makes it easier to scale interactivity.

### Take Advantage of Python Ecosystem

AIPL is also intended to be practical (if only at small scale), so operators are easy to write using the existing cadre of Python libraries, and allow options and parameters passed to them verbatim.

### Keep It Simple

The implementation is intentionally homespun, to remove layers of abstraction and reduce the friction of setup and operation.
It doesn't parallelize anything yet but it still should be able to handle hundreds of items even as it is, enough to prove a concept.
I expect it to be straightforward to scale it to mag 5 (up to a million items) if something takes off.

### Learn and Explore

At the very least, AIPL should be a useful tool to learn, explore, and prototype small-scale data pipelines that have expensive operations like API calls and LLM generation.

## Usage

    export OPENAI_API_KEY=<API_KEY>
    echo '<inputs>' | python3 -m aipl [options] [key=value ...] chains/<script>.aipl

This will run the particular script over the given newline-separated inputs.

Options:

- `-x`: breakpoint (drop into pdb) before each command
- `-d`: show inputs in visidata before each command

### `summarize.aipl`

Here's a prime example, a multi-level summarizer in the "map-reduce" style of langchain:


```
#!/usr/bin/env bin/aipl

# fetch url, split webpage into chunks, summarize each chunk, then summarize the summaries.

# the inputs are urls
!fetch-url

# extract text from html
!extract-text

# split into chunks of lines that can fit in the context window
!split maxsize=8000 sep=\n

# have GPT summary each chunk
!format

Please read the following section of a webpage (500-1000 words) and provide a
concise and precise summary in a few sentences, optimized for keywords and main
content topics. Write only the summary, and do not include phrases like "the
article" or "this webpage" or "this section" or "the author". Ensure the tone
is precise and concise, and provide an overview of the entire section:

"""
{input}
"""

!llm model=gpt-3.5-turbo

# join the section summaries together
!join sep=\n-

# have GPT summarize the combined summaries
!format

Based on the summaries of each section provided, create a one-paragraph summary
of approximately 100 words. Begin with a topic sentence that introduces the
overall content topic, followed by several sentences describing the most
relevant subsections. Provide an overview of all section summaries and include
a conclusion or recommendations only if they are present in the original
webpage. Maintain a precise and concise tone, and make the overview coherent
and readable, while preserving important keywords and main content topics.
Remove all unnecessary text like "The document" and "the author".

"""
{input}
"""

!llm model=gpt-3.5-turbo

!print
```

This is the basic syntax:

- comments start with `#` as the first character of a line, and ignore the whole line.
- commands start with `!` as the first character of a line.
- everything else is part of the prompt template for the previous `!` command.

### Command Syntax

Commands can take arguments and/or keyword arguments, separated by whitespace.

- `!cmd arg1 key=value arg2`

Keyword arguments have an `=` between the key and the value, and non-keyword arguments are those without a `=` in them.

- `!cmd` will call the Python function registered to the `cmd` operator with the arguments given, as an operator on the current value.

- Any text following the command line is dedented (and stripped) and added verbatim as a `prompt=` keyword.
- Argument values may include Python formatting like `{input}`
- Prompt values are not automatically formatted. `!format` will format the prompt.
- !literal will convert its prompt into input without formatting.

The syntax will continue to evolve and become clearer over time as it's used.

Notes:

- an AIPL source file documents an entire pipeline from newline-delimited inputs on stdin (or via `!set-input`) to the end of the pipeline (often `!print`).

- commands always run consecutively and across all inputs.

- if you pass N urls on the command line, the initial input will be an array of urls, and will process them each in turn.

# operators

Each operator refers to a Python function (hyphens become underscores).
All parameters are optional named (`keyword=value`) arguments, separated by whitespace.
Parameter values can include values from the current row, e.g. `{input}`.
These are replaced after parameter parsing, and thus can include whitespace.


## currently available operators

### The Big Guns

- `!llm`: text -> text
- `!llm-embedding`: text or prompt -> embedding

### 
- `!cluster n=10`: cluster rows by embedding into n clusters; add label column

### General Array

- `!take n=1`: take first n rows
- `!sample n=3`: choose sample of n random rows
- `!filter`: keep only rows whose value is True-like
- `!unravel`: collapse into 1D array of scalar strings
- `!name foo`: set name of current column
- `!columns colname1 colname2`: new table with only these columns

### Strings/Text

- `!split sep=\n maxsize=0`: text -> text[], staying under maxsize if possible
- `!split-url`: url -> dict(scheme, netloc, path, params, query, fragment)
- `!join sep=,`: text[] -> text
- `!match <regex>`: text -> bool
- `!format`: format prompt as Python string template and set as input
- `!extract-text`: html -> text
- `!extract-links`: html -> dict(linktext, title, href)[]

### How to get data in and out

- `!fetch-url`: url -> html
- `!fetch-file`: path -> text
- `!print`: print to stdout
- `!json`: convert row to json
- `!save filename.txt`: write to file

#### Database

- `!dbinsert <tablename> extrakey=value`: insert each row into database table
- `!dbdrop <tablename>`: drop database table

## operator implementation

It's pretty easy to define a new operator that can be used right away.
For instance, here's how the `!join` operator might be defined:

```
@defop('join', rankin=1, rankout=0, arity=1)
def op_join(aipl:AIPL, v:List[str], sep=' ') -> str:
    'Concatenate text values with *sep* into a single string.'
    return sep.join(v)
```

- `@defop` registers the decorated function as the named operator.
   - `rankin` is what the function takes as input:
     - `0`: a scalar (number or string)
     - `0.5`: a whole row (dict)
     - `1`: a whole column of values
     - `1.5`: the whole table (array of rows)
   - `rankout` is what the function returns
     - `0`: a scalar value
     - `0.5`: a dict of values
     - `1`: a whole column of values
     - `1.5`: the whole table
   - `arity` for how many operands it takes; only `0` and `1` supported currently

The join operator is `rankin=1 rankout=0` which means that it takes a list of strings and outputs a single string.  Which it does.

- Add the `@expensive` decorator if it has to actually go to the network or use an LLM; this will persistently cache the results in a sqlite database.
   - so running the same inputs through a pipeline multiple times won't keep refetching the same data impolitely, and won't run up a large GPT bill during development.

# Architecture

The fundamental data structure is a Table: an array of hashmaps ("rows"), with named Columns that key into each Row to get its value.

A value can be a string or a number or another Table.

The value of a row is the value in the rightmost column of its table.
The rightmost column of a table is a vector of values representing the whole table.

A simple vector has only strings or numbers.
A simple table has a simple rightmost value vector and is Rank 0.
Each nesting of tables in the rightmost value vector increases its Rank by 1.

## operators
Each operator consumes 0 or 1 or 2 operands (its `arity`), and produces one result, which becomes the operand for the next operator.

Each operator has an "in rank" and an "out rank", which is the rank of the operands they input and output.

By default, each operator is applied across the deepest nested table.
The result of each operator is then placed in the deepest nested table (or its parent).

### rankin=0: one scalar at a time

With `rankin=0` and `rankout` of:

- -1: no change (like 'print')
- 0: scalar operation (like 'translate')
- 0.5: scalar to simple row (like 'split-url')
- 1: scalar to simple vector (like 'split-text')
- 1.5: scalar to table (like 'extract-links')

### rankin=0.5: consume whole row

With `rankin=0.5`, and `rankout` of:

- -1: no change to row (like 'dbinsert')
- 0: add a new value to row (like 'pyexpr')
- 0.5: replace or remove row (like 'filter')
- 1: transform whole vector (like 'sort' or 'normalize')
- 1.5: row to table

### rankin=1: consume the rightmost column

With `rankin=1`, and `rankout` of:

- -1: no change to row (like 'dbinsert')
- 0: reduce to scalar (like 'join')
- 0.5: reduce to simple row (like 'stats')
- 1: transform whole vector (like 'normalize'); or return None to remove column
- 1.5: vector to table

### rankin=1.5: consume whole table

With `rankin=2`, and `rankout` of:

- -1: no change to table
- 0: reduce table to scalar
- 0.5: reduce table to single row (like 'collapse')
- 1: reduce table to single vector ??
- 1.5: replace table with returned table (like 'sort')

## arguments and formatting

In addition to operands, operators also take parameters, both positional and named (`args` and `kwargs` in Python).
These cannot have spaces, but they can have Python format strings like `{value}`.

The identifiers available to Python format strings come from a chain of contexts:

- column names in the current table are replaced with the value in the current row (for rankin=0 or 0.5).
   - from each nested table, in priority from innermost to outermost
- row will also defer to their "parent" row if they don't have the column

# Future

## new operators

- `!define`: create a subchain of operators

- `!group`

- `!dbtable`: use entire table as input
- `!dbquery`: sql template -> table

## single-step debugging

- show results of each step in e.g. VisiData
- output as Pandas dataframe

## simple website scraping

- recursively apply `!extract-links` and `!fetch-url` to scrape an entire website
  - need operators to remove already-scraped urls and urls outside a particular domain/urlbase

## License

I don't know yet.

You can use this and play with it, and if you want to do anything more serious with it, please get in touch.
The [rest](https://bluebird.sh) [of my](https://xd.saul.pw) [work](https://visidata.org) is fiercely open source, but I also appreciate a good capitalist scheme.
Come chat with me on Discord [saul.pw/chat](saul.pw/chat) or Mastodon [@saulpw@fosstodon.org](https://fosstodon.org/@saulpw) and let's jam.

If you want to get updates about I'm playing with, you can [sign up for my AI mailing list](https://landing.mailerlite.com/webforms/landing/y9b3w8).
