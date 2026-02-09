# AIPL Design Notes

## History & Motivation

AIPL started in April 2023 as a reaction to LangChain:

> LangChain is unnecessarily complicated. We shouldn't have to write boilerplate Python for this. And you don't need a vector store if you're only dealing with 100k things. We need a soft layer for AI.

The insight was that AI pipelines are actually straightforward: fetch some data, split it, send it to an LLM, combine the results. The hard part isn't the code -- it's managing the data flow, caching expensive operations, and iterating on prompts. AIPL aimed to make these things trivially easy.

### The Three Thirds

AIPL is 1/3 array language, 1/3 scripting language, 1/3 VisiData. From each:

- **Array language** (APL, K): implicit looping, rank-based dispatch, tacit dataflow. No variable naming, no boilerplate. See [array-notes.md](array-notes.md) for deeper research.
- **Scripting language**: top-to-bottom execution, no ceremony. Natural language (prompts) is the default; commands are secondary. Not a "real" programming language -- a scripting language, and non-programmers know the difference.
- **VisiData**: inspect intermediate results at any step (`--step-vd`), explore data interactively, treat everything as a table.

### Hard/Soft Layers

A key design principle: alternate hard and soft layers.

- **Hard layer** (Python operators): gets robust, reliable, productionizable over time.
- **Soft layer** (AIPL scripts): where experiments happen. Like BASIC, spreadsheets, macros -- things shared on forums, recombined in infinite ways. Business value lives here because businesses need fluidity.

It should be easy to move functionality between layers. Implementing new hard-layer operators should be lightweight, so a cheap naive version can be tested before investing in optimization.

## Language Design

### Data Model

The fundamental structure is a **Table**: an array of rows (hashmaps), with named Columns.

- Values can be strings, numbers, or nested Tables.
- The rightmost column is always the "current output" (floating output column).
- Each operation adds a new column; the last column becomes the next input.
- Columns have string type hints ('text', 'html', 'url') -- not strongly typed, warn but allow.

### Rank System

Operators declare their input and output rank:

| Rank | Meaning | Example |
|------|---------|---------|
| 0 | scalar | `!fetch-url` (one URL at a time) |
| 0.5 | whole row | `!format` (access all columns) |
| 1 | vector (column) | `!join` (reduce column to scalar) |
| 1.5 | whole table | `!sort`, `!filter` |
| None | nothing (source/passthrough) | `!literal`, `!print` |

Rank-based dispatch handles nesting automatically: a rank-0 op applied to nested tables recurses to the deepest level. This is the core insight from APL -- implicit looping eliminates explicit iteration.

### Operator Taxonomy

- **Generators** (niladic): `!literal`, `!python-input` -- produce data from nothing
- **Pipes** (monadic 1:1): `!fetch-url`, `!extract-text` -- transform each value
- **Splits** (1:N): `!split`, `!extract-links` -- one value becomes many
- **Folds** (N:1): `!join`, `!sum` -- many values become one
- **Scans** (N:N): pairwise with accumulator (planned, not fully implemented)

### The Prompt

The unformatted text after each command is its "prompt" -- a key AIPL feature that makes natural language the default:

```
!llm model=gpt-3.5-turbo

Please summarize the following text concisely:

"""
{_}
"""
```

The prompt becomes a `prompt=` keyword argument. It supports multiline text, whitespace, and characters that would be awkward in command arguments. `!format` explicitly formats the prompt with row values; other commands get the prompt as-is.

Design insight (from Adam K): `!format` is actually a dyadic operator where the prompt provides the second operand. This extends to other commands -- if no prompt is present, a second operand could come from `<tablename`.

### Caching

`@expensive` operators cache results in a local SQLite database. This is critical:

- Running the same inputs through a pipeline multiple times doesn't re-fetch or re-query.
- Development iteration is cheap even with expensive API calls.
- Cache is keyed on inputs, so changing the prompt invalidates naturally.

### Column Naming

Columns may be named by the generating operand, or the value column may be left anonymous. Scripts can name/rename columns from tables of arbitrary depth. Values from earlier operands are available to later operators, associated with their actual row.

This is "the big deal" -- making column references work naturally across nested tables of arbitrary depth.

## Architecture Evolution

### v1: Proof of Concept (23-ai, April-May 2023)

Monolithic `ai.py` with basic interpreter. Established:
- The `!command` syntax
- Inline prompt templates
- SQLite caching with `@expensive`
- Core pipeline: fetch -> extract -> split -> LLM -> join

### v2: Production (23-aipl, May-November 2023)

Full rewrite as proper Python package:
- 70+ operators
- Formal rank system with `@defop(rankin=X, rankout=Y)`
- Parser, interpreter, REPL
- Test suite with CI
- Collaborators (Kef, Rowan)
- MIT license
- README.aipl generates README.md (dogfooding!)

Already used as a "paid shovel" for AI tasks by July 2023.

### v3: Unix Experiment (24-aipl2, June 2024)

A radical rethink: what if we don't need a DSL at all? See [v2-unix-experiment.md](v2-unix-experiment.md).

Key ideas:
- Each operator invocation is a separate `aid` command, composed with Unix pipes
- JSONL streaming between stages (inspectable with standard tools)
- Python type hints replace the rank system (inspect-driven dispatch)
- `LastAttrDict` with `_` key for implicit "previous result" reference
- Dual I/O: TTY mode caches to timestamped files; pipe mode streams to stdout

The tradeoff: gained simplicity and Unix tool integration, lost the "see the whole pipeline in one file" clarity.

## Design Decisions

### stdin behavior
- stdin produces a single `[1]` input, not automatic splitlines
- All args/kwargs are formatted; the prompt following is unformatted

### !def
- `!def` (later `!!def`) creates composite operators from indented sub-commands
- Considered renaming to `!aipl` (unary), consuming prompt as input

### Error handling
- Open question: how to discard rows with errors during "production" while making errors loud during development?

### Streaming
- Question raised May 2023: does it need to be built for streaming from the start?
- "Stream-like computation could be expressed by generalizing array types to allow an unbounded dimension." (from Typed J paper)

### Webapp
- Simple Flask design: GET /sheet/<id> for static HTML, POST /api/run to execute AIPL with JSON return
- Never completed beyond prototype

## Future Ideas

### Unimplemented Operators
- `!defpy`: inline Python with row data as locals (see [array-notes.md](array-notes.md))
- `>>tablename` and `<<tablename`: table save/load shorthand
- `!scan`: incremental pairwise processing with accumulator

### Tooling
- Jupyter kernel
- Simple web interface (beyond the Flask prototype)
- Operator documentation generator (`defop doc generator`)

### Bigger Vision
- Build catalog of operators and chains as institutional memory
- Find one-person businesses automatable with AI; document processes as AIPL scripts
- Sell turnkey franchises: person + market taste + AIPL scripts = viable business

### From the v3 Experiment
- Consider whether Unix pipe composition could coexist with .aipl scripts
- The `LastAttrDict` pattern (implicit previous-result reference) could simplify the rank system
- Type-hint-driven dispatch is worth exploring as alternative to explicit rank declarations

## Team Roles (Historical)

When AIPL was envisioned as a team project:
- Array language nerd (core/operators)
- AI/data enthusiast (operators/scripts)
- Data engineer (infra/scripts)
- Web dev (frontend)
- QA (tests/docs)
- Librarian (docs/community)
- Plus business roles if monetizing

## Key References

- [OpenAI ChatML](https://github.com/openai/openai-python/blob/main/chatml.md) -- underlying ChatGPT input format
- [Typed J paper](https://www.ccs.neu.edu/home/jrslepak/typed-j-full.pdf) -- array type theory
- [APL Array Model](https://aplwiki.com/wiki/Array_model) -- nested vs flat array theory
- [General Arrays paper](https://dl.acm.org/doi/pdf/10.1145/586656.586663) -- Box/Enclose operators
- [K language intro](http://www.math.bas.bg/bantchev/place/k.html) -- K equivalents of AIPL operations
