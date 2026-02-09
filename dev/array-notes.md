# Array Language Research Notes

Notes from studying APL, K, and array theory to inform AIPL's design.

## Enclose/Disclose (Box/Unbox)

From [A Based System for General Arrays](https://dl.acm.org/doi/pdf/10.1145/586656.586663):

In both Floating System and Grounded System:
- `pp<A -> 0` -- enclosed A has 0 dimensions
- `><A -> A` -- enclose+disclose are inverses
- `>S -> S` -- disclosed scalar is just the scalar

The key difference: in Floating System, `<S <-> S` (enclosed scalar is the scalar), but in Grounded System `<S != S`.

### Enclose (from GPT-4 summary)

- Creating nested arrays: represent hierarchical data or multi-level groups
- Partitioning arrays: `(partition with enclose)` to split arrays based on conditions

### Disclose

- Extracting elements: "flattening" nested structure by one level
- Combining: concatenating contents of nested arrays along an axis

### Nest

`Nest` applies Enclose only if the argument is simple. Useful when a nested array is expected but a simple one might be supplied.

## Nested vs Flat Array Theory

From [APL Wiki](https://aplwiki.com/wiki/Array_model#Flat_array_theory):

> In nested APLs each individual number or character is encapsulated in a simple scalar. Arrays which contain only simple scalars are called simple. Non-simple arrays are called "nested".

> The programmer can Pick an element of an array directly. The resulting element is always an array, even for simple arrays: Pick never returns something which is "just a number".

This is relevant to AIPL: every value in a Table is conceptually "boxed" -- it might be a scalar or another Table. The rank system controls how deeply operators recurse into this nesting.

## K Language Comparisons

From [K intro](http://www.math.bas.bg/bantchev/place/k.html):

### Join strings with separator

K: `2_,/", ",/:x` -- append separator to each, join all, drop leading separator

AIPL: `!join sep=,\s`

The K version requires understanding three verbs and two adverbs. AIPL's named-parameter style is immediately readable.

### Flatten a nested list

K: `,//` -- join-over applied repeatedly until stable

AIPL: `!flatten`

The K version is elegant but cryptic. Both converge to the same result.

## Inline Python Idea (Unimplemented)

```
!defpy join sep=\s
sep.join(input)

!defpy split sep=\s
input.split(sep)
```

Provide entire row as locals, along with globals set with `!global`. This would allow quick operator prototyping without writing a full `@defop` function. Never implemented -- the existing `!python` and `!python-expr` operators partially cover this.
