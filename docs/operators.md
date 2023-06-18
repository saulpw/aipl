
## An AIPL script is essentially a list of operators.

When an AIPL script is executed, each operator is applied in sequence over all rows in the input.

Each operator uses 0, 1, or 2 operands to perform a certain operation and produce a resulting value.  These are called "nonary", "unary", and "binary" operators.
Some operators may be "ambinary", and are able to be applied as either unary or binary operators.

## The input

There is always a "most recent" value, which is the toplevel result of the previously applied operator.
This value is commonly called the "input", and it provides the set of default operands for the next operator if it is unary, or the default "left" operands if the next operator is binary.

(An operator that does not produce a result is a "tap", presumably having some desirable side-effect.  It may use its input operands but must not modify them.)

## The output

The operator is applied across the input rows, and these outputs are aggregated into a single "result", which immediately becomes the next "input".

The result can be assigned to a name with a special argument that starts with `>>`, e.g. `!join>>foo`.

A single `>`, e.g. `>bar`, is used to assign a name to the bottommost column(s) of scalars, which are then available for formatting as `{bar}` in arguments and elsewhere.

## Tacit dataflow

This completely tacit dataflow is great for unary (and nonary) operators.

For binary operators, the second or "right" operand can be passed as a special argument, e.g. `!cross <foo`.  `foo` must have been a previous result named with `>>`.

Alternatively, the text on the lines following the operator, commonly called "the prompt", will be passed as the second operand.  For unary operators, if there is any non-whitespace text in the prompt, the prompt will override the default input and be passed as the first operand instead.  The result of this operator becomes the input, so the previous result must be named or it will be lost forever!!

A lone `<` as as argument signifies that everything until the end of the line is taken to be the prompt.

If `<` is at the end of a !command line, then a prompt is expected, so and the REPL will read text until EOF.
(In non-REPL mode, `<\n!` would force the input operand to be an empty string.

## Tacit looping

The input may have as many as 99 dimensions, but operand(s) can only have 0 or 1 dimensions (until actual matrix operations are implemented, but then the limit would be 2).

Each operator must specify the dimensionality of its operands (using defop kwargs `rankin` and `rankin2`).

### Unary operators
When a unary operator is applied to an input with higher dimensionality, the operator will be applied recursively to each of the input's values.
The result will have the same "outer" structure as the input, while the "innermost" values will the output values of the operator.

Each row containing the input value with the lowest dimensionality will be augmented with the output of the operator applied to it.

A column will be added to the tables containing those rows, such that the row and table values will now be these most recent results.

### Binary operators

The right operand must be a scalar or a toplevel output (for now).
If needed, looping over the right operand must be done manually by the operator.

## Rows and columns

All scalars and vectors are actually projections of "rows" and "tables", respectively.  The "value" of a row is a (boxed) scalar or another table.  A "simple row" has a scalar value.  The value of a table is a vector of the values of its rows.  A simple table has a value that is a vector of scalars.

A simple row is like `0-plus` or `0.5` dimension.  A simple table is like `1-plus` or `1.5` dimension.

A opaque row can have other potential data besides its value.
A column knows how to get a particular projection of data from a opaque row.

A table is a list of opaque rows and a list of columns.
The table can generate a list of virtual rows, one for each opaque row, which appear as mappings from column names to values.

A row can be part of many tables.
Each column is on only one table, but a specific opaque row can be part of many tables.

The opaque row contains all the data, so both columns and tables can be lightweight objects.
If rows are augmented but never need to be copied, then generating both column- and row-wise subsets of tables is a lightweight process.

## Tacit context of previous results

As a row is augmented by the continued application of operators, and its value changes, the tables it is part of

