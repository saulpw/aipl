# AIPL v2: Unix Pipeline Experiment (June 2024)

A rethinking of AIPL as a Unix tool instead of a DSL interpreter. Written as `aid`, a single Python CLI script. Local experiment only (never published).

## Motivation

After 6 months of AIPL-the-language, the question: do we need a custom parser, interpreter, and rank system? What if each operator were just a standalone command, composed with shell pipes?

## Architecture

```bash
# Instead of a .aipl file:
aid new url=https://en.wikipedia.org/wiki/Sega_Genesis
aid add complinks.txt
aid read
aid text
aid split maxsize=8000
aid format prompt=prompt1.txt
aid llm
aid parse
```

Each invocation of `aid` runs one command. State passes between invocations via JSONL files.

### Data Format

Rows are JSON objects streamed as JSONL (one JSON object per line). Each command reads rows from stdin (or cached file) and writes enriched rows to stdout (or cached file).

### Smart I/O

- **TTY mode** (no pipe): reads from previous cache file, writes to timestamped file, renames on success (atomic output)
- **Pipe mode**: reads stdin, writes stdout
- This means: run `aid read` interactively and it picks up where it left off. Pipe it and it streams.

### Type-Driven Dispatch

Instead of explicit rank declarations, Python type hints drive routing:

```python
def cmd_read(self, url:str, **kwargs):       # scalar: called per-value
def cmd_split(self, v:str, sep=None):        # scalar: called per-value, yields multiple
def cmd_extract_links(self, html:str):       # scalar: yields dicts
def cmd_parse(self, row:dict):               # row: called per-row
def cmd_add(self, rows:list, *args):         # list: called once with all rows
def cmd_help(self, rows:None):               # None: no input needed
```

The `call()` function inspects the first parameter's type hint and routes accordingly. Generator functions fan out automatically.

### LastAttrDict

The key data structure innovation:

```python
class LastAttrDict(dict):
    def keys(self):
        return ['_'] + list(super().keys())
    def __getitem__(self, k):
        if k == '_':
            return super().__getitem__(list(super().keys())[-1])
        return super().__getitem__(k)
```

`row['_']` always returns the most recently added field's value. This elegantly solves the "previous result" problem without needing AIPL's floating-output-column mechanism.

### Field Routing

Explicit input/output field naming via CLI syntax:

```bash
aid cmd <input_field >output_field
aid read <url >html
```

The `<` and `>` prefixes specify which field to read from and write to.

### Database Caching

`@dbcache` decorator wraps expensive operations:

```python
@dbcache
def cmd_read(self, url:str, **kwargs):
    return trafilatura.fetch_url(url)
```

Results cached in SQLite by function name + args hash. Same principle as AIPL's `@expensive`.

## What Worked

- **Simplicity**: no parser, no interpreter, no rank system. Just Python methods + inspect.
- **Inspectability**: `cat output.jsonl` to see intermediate results. Standard Unix tools work.
- **Composability**: natural integration with grep, awk, jq, xargs.
- **Atomic output**: timestamped files prevent data loss on errors.

## What Was Lost

- **Pipeline visibility**: a .aipl file shows the whole pipeline at a glance. A Makefile or shell script is noisier.
- **Prompt integration**: inline prompts are AIPL's killer feature. Shell quoting makes multi-line prompts awkward.
- **Rank semantics**: type hints handle simple cases but can't express AIPL's nested-table recursion.
- **Cohesion**: AIPL chains are self-contained documents. Shell pipelines scatter context.

## Key Takeaway

The rank system is more powerful than type hints for nested data, but type hints are sufficient for flat pipelines. The `LastAttrDict` pattern and inspect-driven dispatch are worth considering as simplifications where full rank semantics aren't needed.
