# AIPL (Array-Inspired Pipeline Language)

A smolchain to make it easier to explore and experiment with AI pipelines.

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
Passing data implicitly between operators allows for efficient representation of data flows, and avoids [one of the hardest problems in computer science](naming things).
The implicit looping of array languages makes it easier to scale interactivity.

### Take Advantage of Python Ecosystem

AIPL is also intended to be practical (if only at small scale), so all operators are written using the existing cadre of Python libraries, and allow options and parameters passed to them verbatim.

### Keep It Simple

The implementation is intentionally homespun, to remove layers of abstraction and reduce the friction of setup and operation.
It doesn't parallelize anything yet but it still should be able to handle hundreds of items even as it is, enough to prove a concept.
I expect to be able to scale it up to a million items if something takes off.

### Learn and Explore

At the very least, AIPL should be a useful tool to learn, explore, and prototype small-scale data pipelines that have expensive operations like API calls and LLM generation.


## Usage

    python3 -m aipl <inputs> < chain/<script>.aipl



### `summarize.aipl`

Here's a seminal example, a multi-level summarizer in the "map-reduce" style of langchain:


```
#!/usr/bin/env aipl

# fetch url(s), split webpage into chunks, summarize each chunk, then summarize the summaries.
# Usage: $0 <url> [...]

!fetch-url

# extract text from html
!extract-text

# split into chunks of lines that can fit in the context window
!split maxsize=8000 sep=\n

# have GPT summarize each chunk
!llm model=gpt-3.5-turbo

Please read the following section of a webpage (500-1000 words) and provide a concise and precise summary in a few sentences, optimized for keywords and main content topics. Write only the summary, and do not include phrases like "the article" or "this webpage" or "this section" or "the author". Ensure the tone is precise and concise, and provide an overview of the entire section:

"""
{input}
"""

# join the section summaries together
!join sep=\n-

# have GPT summarize the combined summaries

!format
Based on the summaries of each section provided, create a one-paragraph summary of approximately 100 words. Begin with a topic sentence that introduces the overall content topic, followed by several sentences describing the most relevant subsections. Provide an overview of all section summaries and include a conclusion or recommendations only if they are present in the original webpage. Maintain a precise and concise tone, and make the overview coherent and readable, while preserving important keywords and main content topics.  Remove all unnecessary text like "The document" and "the author".

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

- `!cmd` will call the Python function `op_cmd` with the arguments given, as an operator on the current Box.

- Any text following the command line is dedented (and stripped) and added verbatim as a `prompt=` keyword.
- Argument values may include Python formatting like `{input}`
- Prompt values are not automatically formatted. `!format` will format the prompt.
- !literal will convert its prompt into input without formatting.

The syntax will continue to evolve and become clearer over time as it's used.

Notes:

- an AIPL source file documents an entire pipeline from the input CLI args (or `!set-input`) to the end of the pipeline (often `!print` or `!print-json`).

- commands always run consecutively and across all inputs.

- if you pass N urls on the command line, the initial input will be an array of urls, and will process them each in turn.

# operators

Each operator refers to a Python function (hyphens become underscores).
All parameters are optional named (`keyword=value`) arguments, separated by whitespace.
Parameter values can include values from the current row, e.g. `{input}`.
These are replaced after parameter parsing, and thus can include whitespace.


## currently available operators

- `!set-input`: replace current input with inline input
- `!fetch-url`: url -> html
- `!extract-text`: html -> text
- `!split`: text -> text[]
- `!join`: text[] -> text
- `!llm`: text or prompt -> text
- `!flatten`: collapse into 1D array of scalar strings
- `!match <arg>`: text -> 0 if not found in match arg/p or 1 if match
- `!filter`: text -> 0 if not found in match arg/p or 1 if match

- `!vd`: open in visidata

## operator implementation

It's really easy to define a new operator that can be used right away.
For instance, here's how the `!fetch-url` operator could be defined (in actuality it includes a few extra niceties, like removing the anchor from the url):

```
@op_scalar
@expensive
def fetch_url(db:Database, df:LazyDataframe, row:LazyRow, **kwargs) -> str:
    import trafilatura
    return trafilatura.fetch_url(row.input, **kwargs)
```

- `@op_scalar` means that it applies to a single row, and returns a single output; a simple mapping.
- `@expensive` because it has to actually go to the network; so we want to persistently cache the results in our database.
   - thus running the same inputs through a pipeline multiple times won't keep refetching the same data impolitely, and won't run up a large GPT bill during development.
- Even a scalar operation can access to the Database and the entire Dataframe.

### operator types

- `@op_scalar`: take a single value, return a single value
- `@op_expand`: take a single value, can generate multiple values
   - result is a new dataframe for each input row
   - scalar functions iterate on the rows in the deepest dataframe
- `@op_reduce`: take a dataframe and reduce it to a single value
- `@op_replace`: take a dataframe and replace it with a new dataframe with a different schema (e.g. grouping)
- (soon) `@op_scan`: take incremental slices of a dataframe and generate a single value

# Future

## new operators

- `!format`: prompt template -> text
- `!llm-embedding`: text -> embedding

- `!name` and `!ref`
- `!define`: create a subchain of operators

- `!group`
- `!first`

- `!dbinsert`: insert row into database
- `!dbtable`: use entire table as input
- `!dbquery`: sql template -> table

- `!extract-links`: html -> url[]

## single-step debugging

- show results of each step in e.g. VisiData
- output as Pandas dataframe

## simple website scraping

- recursively apply `!extract-links` and `!fetch` to scrape an entire website
  - need operators to remove already-scraped urls and urls outside a particular domain/urlbase

## License

I don't know yet.

You can use this and play with it, and if you want to do anything more serious with it, please get in touch.
The [rest](bluebird.sh) [of my](xd.saul.pw) [work](visidata.org) is fiercely open source, but I also appreciate a good capitalist scheme.
Come chat with me on Discord [saul.pw/chat](saul.pw/chat) or Mastodon [@saulpw@fosstodon.org]() and let's jam.
All ages and genders and races welcome.
