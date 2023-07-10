
# Design

AIPL is intended as a simple platform for quick proof of concept data pipelines to be implemented and tested.

## Why?

The recent developments in LLMs and AI are a whole new level of capabilities (and costs).
I wanted to see what all the fuss was about, so I tried to do some basic things with [langchain](https://github.com/hwchase17/langchain) but it was this big complicated system.
So instead I implemented some small workflows myself with raw Python, and it turned out that AI is actually pretty straightforward.
This is a small hackable platform that makes it easy to experiment and get small-scale results.
It's called AIPL.

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

## What is "implicit looping"?

a concept borrowed from APL.

Yes, APL, that language from the 60s that looks like this:

```
avg ← +⌿ ÷ ≢
```

Now before you run away screaming, there are 3 big ideas in APL, and why Iverson won the Turing Award in 1980:

1. implicit looping and tacit programming

    - brilliant, removes a large amount of code.  beyond just the loops too

2. symbols

APL uses a special set of non-text symbols, a custom alphabet that nearly predates ASCII itself.
This is why it looks like alien gibberish to the uninitiated, and why APL has all but died out.
[Iverson's paper and talk for the Turing Award is entitled [Notation as a Tool of Thought]()
so "notation" is ironically the focus *and* the fallacy of APL.]

The symbology is math-based (as APL is a language for teaching and doing linear algebra), and is elegantly designed. but the idea is unfortunately a non-starter for modern adoption.

People think in *words* or word-like chunks, and while letters of the alphabet make up the words, they are only symbols, and they carry zero semantic content.
Learning a new alphabet (and one with combinatoric semantics) is a huge barrier to learning a new language.

Now, I agree with Iverson's fundamental premise, that a sub-verbal facility with a core set of operations, is a tremendous tool for thought.
But the actual terse and non-verbal notation ultimately prevented APL from being in common use.

3. vocabulary

APL defines an elegant core set of operators that are just the right level of abstraction for math, particularly linear algebra.
This is why APL-like languages are still used in the finance world: you can get a lot done quickly, and with very little code, when you know the domain and the operators are at the right level of abstraction and you can fit them in your head.

The real art of software is in developing a set of legos that are easily explainable and interoperate well together, conforming to an intuitive yet precisely-defined connection spec.
When done well, these legos are composable without anything else necessary to bind one's input to the other's output.  Then tacit programming becomes not just possible but desired.

---

Thus, AIPL borrows implicit looping and tacit programming from APL, and lets go of its alien symbology.
AIPL also borrows some of APL's vocabulary, but since data pipelines are a much different domain than math (and much more has been developed in the data domain over the past 50 years), we need to develop a different set of operators.

So AIPL is also a *vocabulary discovery platform*.
It is easy to add new operations in Python.
AIPL is really just a skin over Python; a notebook in script form.

## For "port-able" prototypes

Once you have the operators in the right order and with the right parameters, it's "just" engineering to call them at the right time, with the right batch size, in the right format, caching the results, etc.
You have a "script", like for a movie.

You still have to do all the engineering; you have to put it into production.
But with the script, you know what's required, and you can start to plan out the process of development.

You can *port* it.

Don't over-engineer your experiments and your prototypes.
Just put legos together in a logical order and see how the whole chain works.
Tune, iterate, and discover quickly if your idea is viable or not.

# The Design


# Design

Operators take 0, 1, or 2 "operands with dimensionality", and any number of scalar (int/float/str) parameters.

These "operands with dimensionality" are used like arrays in traditional array languages.
However, those have multidimensional arrays of scalars, whereas AIPL operands are more like nestable database tables.

These tables have:

- a list of "rows"
- named columns that can be reordered and removed without updating each row
- homogenous types within a column (possibly NULL)
- heterogenous types within a row

Every operator consumes 0, 1, or 2 operands and produces exactly 1 operand.
(Some operators have only side-effects and don't actually do anything to the data; these take 1 operand and return the same.)

The simplest operator implementation takes 0/1/2 tables and returns a table.
The return table may be one of the unmodified input operands, otherwise it must be a new table.
The rows may be referenced for efficiency.

These operators must use the consistent pattern for iterating over the table's dimensions correctly, only "changing" the proper dimension (by default the last dimension).

Tables are more complex than simple vectors.
But ideally, an operator could be defined only by its smallest operation, and a decorator(?) would do the consistent iteration.

split iterates over its input, and where it finds a string, returns a 1 column table.
where it finds an int/float, it errors or returns the int.
where it finds a table, it recurses.

take:
   where it finds a simple table, returns a table with only N rows

join:
   a simple table of strings, returns a string

parse-url:
   a url string, returns a table with 1 row

unravel:
   a table of simple tables, returns a simple table

filter:
   a table with a bool value column; returns a table without that column, with only rows for which that column was true


