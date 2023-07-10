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

### `summarize.aipl`

Here's a prime example, a multi-level summarizer in the "map-reduce" style of langchain:

```
#!/usr/bin/env bin/aipl

# fetch url, split webpage into chunks, summarize each chunk, then summarize the summaries.

# the inputs are urls
!read

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
{_}
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
{_}
"""

!llm model=gpt-3.5-turbo

!print

```

## Usage

```
usage: aipl [-h] [--debug] [--test] [--interactive] [--step STEP] [--step-breakpoint] [--step-rich] [--step-vd] [--dry-run] [--cache-db CACHEDBFN] [--no-cache]
            [--output-db OUTDBFN] [--split SEPARATOR]
            [script_or_global ...]

AIPL interpreter

positional arguments:
  script_or_global      scripts to run, or k=v global parameters

options:
  -h, --help            show this help message and exit
  --debug, -d           abort on exception
  --test, -t            enable test mode
  --interactive, -i     interactive REPL
  --step STEP           call aipl.step_<func>(cmd, input) before each step
  --step-breakpoint, -x
                        breakpoint() before each step
  --step-rich, -v       output rich table before each step
  --step-vd, --vd       open VisiData with input before each step
  --dry-run, -n         do not execute @expensive operations
  --cache-db CACHEDBFN, -c CACHEDBFN
                        sqlite database for caching operators
  --no-cache            sqlite database for caching operators
  --output-db OUTDBFN, -o OUTDBFN
                        sqlite database accessible to !db operators
  --split SEPARATOR, --separator SEPARATOR, -s SEPARATOR
                        separator to split input on

```

## Command Syntax

This is the basic syntax:

- comments start with `#` as the first character of a line, and ignore the whole line.
- commands start with `!` as the first character of a line.
- everything else is part of the prompt template for the previous `!` command.

Commands can take positional and/or keyword arguments, separated by whitespace.

- `!cmd arg1 key=value arg2`

Keyword arguments have an `=` between the key and the value, and non-keyword arguments are those without a `=` in them.

- `!cmd` will call the Python function registered to the `cmd` operator with the arguments given, as an operator on the current value.

- Any text following the command line is dedented (and stripped) and added verbatim as a `prompt=` keyword argument.
- Argument values may include Python formatting like `{input}` which will be replaced by values from the current row (falling back to parent rows, and ultimately the provided globals).
- Prompt values, on the other hand, are not automatically formatted. `!format` go over every leaf row and return the formatted prompt as its output.
- !literal will set its prompt as the toplevel input, without formatting.

The AIPL syntax will continue to evolve and be clarified over time as it's used and developed.

Notes:

- an AIPL source file documents an entire pipeline from newline-delimited inputs on stdin (or via `!literal`) to the end of the pipeline (often `!print`).
- commands always run consecutively and across all inputs.
- the initial input is a single string (read from stdin).

## List of operators

- `!abort` (in=None out=None)
   Abort the current chain.
- `!cluster` (in=1 out=1)
   Cluster rows by embedding into n clusters; add label column.
- `!columns` (in=1.5 out=1.5)
   Create new table containing only these columns.
- `!comment` (in=None out=None)
   Do nothing (ignoring args and prompt).
- `!cross` (in=0.5 out=1.5)
   Construct cross-product of current input with given global table
- `!global` (in=100 out=1.5)
   Save toplevel input into globals.
- `!unbox` (in=1.5 out=1.5)
   None
- `!csv-parse` (in=None out=1.5)
   Converts a .csv into a table of rows.
- `!dbopen` (in=None out=0)
   Open connection to database.
- `!dbquery` (in=0.5 out=1.5)
   Query database table.
- `!dbdrop` (in=None out=None)
   Drop database table.
- `!dbinsert` (in=0.5 out=None)
   Insert each row into database table.
- `!option` (in=None out=None)
   Set option=value.
- `!debug` (in=None out=None)
   set debug flag and call breakpoint() before each command
- `!def` (in=0 out=None)
   Define composite operator from cmds in prompt (must be indented).
- `!extract-text-all` (in=0 out=0)
   Extract all text from HTML
- `!extract-text` (in=0 out=0)
   Extract meaningful text from HTML
- `!extract-links` (in=0 out=1.5)
   Extract (linktext, title, href) from <a> tags in HTML
- `!filter` (in=1.5 out=1.5)
   Return copy of table, keeping only rows whose value is Truthy.
- `!format` (in=0.5 out=0)
   Format prompt text (right operand) as a Python string template, substituting values from row (left operand) and global context.
- `!groupby` (in=1.5 out=1.5)
   Group rows into tables, by set of columns given as args.
- `!require-input` (in=100 out=100)
   Ensure there is any input at all; if not, display the prompt and read input from the user.
- `!join` (in=1 out=0)
   Join inputs with sep into a single output scalar.
- `!json` (in=100 out=0)
   Convert Table into a json blob.
- `!json-parse` (in=0 out=1.5)
   Convert a json blob into a Table.
- `!literal` (in=None out=0)
   Set prompt as top-level input, without formatting.
- `!llm` (in=0 out=0)
   Send chat messages to `model` (default: gpt-3.5-turbo).  Lines beginning with @@@s or @@@a are sent as system or assistant messages respectively (default user).  Passes all named args directly to API.
- `!llm-embedding` (in=0 out=0.5)
   Get a [text embedding](https://platform.openai.com/docs/guides/embeddings/what-are-embeddings) for a string from `model`: a measure of text-relatedness, to be used with e.g. !cluster.
- `!match` (in=0 out=0)
   Return a bool with whether value matched regex. Used with !filter.
- `!metrics-accuracy` (in=1.5 out=0)
   None
- `!metrics-precision` (in=1.5 out=0)
   None
- `!metrics-recall` (in=1.5 out=0)
   None
- `!name` (in=1.5 out=1.5)
   Rename current input column to given name.
- `!nop` (in=None out=None)
   No operation.
- `!pdf-extract` (in=0 out=0)
   Extract contents of pdf to value.
- `!print` (in=0 out=None)
   Print to stdout.
- `!python` (in=None out=None)
   exec() Python toplevel statements.
- `!python-expr` (in=0.5 out=0)
   Add columns for Python expressions.
- `!python-input` (in=0 out=1.5)
   eval() Python expression and use as toplevel input table.
- `!ravel` (in=100 out=1.5)
   All of the leaf scalars in the value column become a single 1-D array.
- `!read` (in=0 out=0)
   Return contents of local filename.
- `!read-bytes` (in=0 out=0)
   Return contents of URL or local filename as bytes.
- `!ref` (in=1.5 out=1.5)
   Move column on table to end of columns list (becoming the new .value)
- `!regex-capture` (in=0 out=0.5)
   Capture from prompt regex into named matching groups.
- `!regex-translate` (in=0 out=0)
   Translate input according to regex translation rules in prompt, one per line, with regex and output separated by whitespace:
        Dr\.? Doctor
        Jr\.? Junior
    
- `!replace` (in=0 out=0)
   Replace `find` in all leaf values with `repl`.
- `!sample` (in=1.5 out=1.5)
   Sample n random rows from the input table.
- `!save` (in=0 out=None)
   Save to given filename.
- `!sh` (in=0 out=1.5)
   Run the command described by args.  Return (retcode, stderr, stdout) columns.
- `!shtty` (in=None out=0.5)
   Run the command described by args.  Return (retcode, stderr, stdout) columns.
- `!sort` (in=1.5 out=1.5)
   Sort the table by the given columns.
- `!grade-up` (in=1.5 out=1)
   Assign ranks to unique elements in an array, incrementally increasing each by its corresponding rank value.
- `!split` (in=0 out=1)
   Split text into chunks based on sep, keeping each chunk below maxsize.
- `!split-into` (in=0 out=0.5)
   Split text by sep into the given column names.
- `!take` (in=1.5 out=1.5)
   Return a table with first n rows of `t`
- `!test-input` (in=100 out=1.5)
   In test mode, replace input with prompt.
- `!test-equal` (in=0 out=None)
   In test mode, error if value is not equal to prompt.
- `!test-json` (in=100 out=None)
   Error if value Column is not equal to json blob in prompt.
- `!url-split` (in=0 out=0.5)
   Split url into components (scheme, netloc, path, params, query, fragment).
- `!url-defrag` (in=0 out=0)
   Remove fragment from url.
- `!xml-xpath` (in=0 out=1)
   Return a vector of XMLElements from parsing entries in value.
- `!xml-xpaths` (in=0 out=0.5)
   Return a vector of XMLElements from parsing entries in value; kwargs become column_name=xpath.
- `!aipl-ops` (in=0 out=0)
   None


## Defining a new operator

It's pretty easy to define a new operator that can be used right away.
For instance, here's how the `!join` operator might be defined:

```
@defop('join', rankin=1, rankout=0)
def op_join(aipl:AIPL, v:List[str], sep=' ') -> str:
    'Concatenate text values with *sep* into a single string.'
    return sep.join(v)
```

- `@defop(...)` registers the decorated function as the named operator.
   - `rankin`/`rankout` indicate what the function takes as input, and what it returns:
     - `0`: a scalar (number or string)
     - `0.5`: a whole row (a mapping of key/value pairs)
     - `1`: a vector of scalar values (e.g. `List[str]` as above)
     - `1.5`: a whole Table (list of the whole table (array of rows)
     - `None`: nothing (the operator is an input "source" if rankin is None; it is a pass-through if rankout is None)
   - `arity` is how many operands it takes (only `0` and `1` supported currently)

The join operator is `rankin=1 rankout=0` which means that it takes a list of strings and outputs a single string.

- Add the `@expensive` decorator to operators that actually go to the network or use an LLM; this will persistently cache the results in a local sqlite database.
   - running the same inputs through a pipeline multiple times won't keep refetching the same data impolitely, and won't run up a large bill during development.

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
- 0.5: scalar to simple row (like 'url-split')
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
These cannot have spaces, but they can have Python format strings like `{input}`.

The identifiers available to Python format strings come from a chain of contexts:

- column names in the current table are replaced with the value in the current row (for rankin=0 or 0.5).
   - from each nested table, in priority from innermost to outermost
- row will also defer to their "parent" row if they don't have the column

# Future

## new operators

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
