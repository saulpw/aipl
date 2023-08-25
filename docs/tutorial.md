# AIPL tutorial

Okay so you heard about this AIPL thing and you're curious to see if the claims hold true.
Are array languages really as powerful as they say?
Can you really prototype an AI pipeline (or any data pipeline) in a few minutes?

Well let's put it to the test.
For this little experiment, I wanted to see how good GPT is at solving the 8 puzzles from [Hanukkah of Data](https://hanukkah.bluebird.sh/5783).
Now, I've already tried pasting one of them into the ChatGPT web interface, so I have an idea how this could work.
(First, if you haven't yet, [install AIPL]()).

    # read Hannukah of Data puzzle from the web
    !read
    https://hanukkah.bluebird.sh/5783/1
    !extract-text
    !print

Okay so first off, there's no boilerplate here.  An AIPL script is just a list of commands (called "operators" hereafter), in order, one after the other.
Each of these operates on the input, and generates an output which becomes the next input.

Here's the toplevel syntax of AIPL:

    - Lines that start with `#` are comments, and ignored.
    - Lines that start with `!` are AIPL command lines, which contain one or more operators and their arguments.
    - All operators start with `!`.
    - All lines after a command line, if there are any, are the "verbatim input", which is passed verbatim to the operator instead of the previous input.

So in this case, `!read` is the operator that reads a URL or file into memory, and it's passed the URL of the first puzzle.
`!extract-text` takes HTML and, um, extracts the text from it.  `!print` prints it to stdout.

We can now run this script:

    aipl hod5783.aipl

and it should work, no questions asked.

## inspecting the pipeline

If you want to see what is happening at each step, you can use `--step rich`:

    aipl hod5783.aipl --step rich

And then before every command, it will dump the input table using the [rich]() text library.

## going bigger

Okay, that's pretty cool, but ultimately we're going to want to do this for all 8 puzzles.

    !split
    1 2 3 4 5 6 7 8

    !format
    https://hanukkah.bluebird.sh/5783/{_}

    !read
    !extract-text
    !print

The `!split` operator splits its input into a list, just like in Python.

`!format` formats its input using [Python string formatting](), and can refer to previous elements by their names (discussed later), or the immediate previous input with `_`.

Now `!read` takes that formatted link (since it has no verbatim input anymore), and then `!extract-text` and `!print` work as before.  If we run it again, we now we get the text of all 8 puzzles.

## array languages

So, uh, that was kind of too easy.  What's going on here?  Where's the loop?  Is this even programming, bro?

Okay, so, the thing about array languages, is that they automatically iterate over their input.  It's called "[loopless programming]()".
Think of the input as an N-dimensional (jagged) list: a list of elements, each of which may also be a list, etc.

The scalar operators we've seen so far--which take a scalar value, usually a string, and return a scalar value, also usually a string--loop over the "last" dimension, or the deepest list.
After a scalar operator is applied, its output has the same structure as the input.

The `!split` operator, on the other hand, is not a scalar operator.  It takes a string, but it returns a list of strings--so the input grows by one dimension.

In array-land the number of dimensions of an operand is called its "rank", with rank of 0 meaning "scalar".
So in our above example, the `!split` takes its verbatim input (a 1-dimensional list of 1 string), and splits
it into a 2-dimensional list: a list of 1 element, which is a list of 8 strings.
Every subsequent operator just operates over all the scalar elements in the list of lists.

## using GPT

Okay, so we've extracted the text, now what?  Well, let's see if GPT can solve the puzzle:

    !format
    I have a database with 4 tables (field names given inside parens):

    - customers (customerid,name,address,citystatezip,birthdate,phone)
    - orders (orderid,customerid,ordered,shipped,items,total)
    - products (sku,desc,wholesale_cost)
    - orders_items (orderid,sku,qty,unit_price)

    Here is a database puzzle to be solved using the above schema:

    """
    {_}
    """

    Give only a SQLite SELECT query to answer the question.

    !llm model=gpt-3.5-turbo

    !print

I wrote a prompt and inserted the extracted text with heavy delimiters, as recommended by the prompt experts. (Who knows if this does anything?  I sure don't.)  But we're clearly asking for a SQL answer from GPT.

Note here that AIPL operators can take arguments, both positional and keyword, like in Python.
These arguments don't have to be quoted--only if they have spaces or quotes or a few other characters (which can be escaped like in C or Python as usual).

To run this script, you'll need to make sure you have the `OPENAI_API_KEY` and `OPENAI_API_ORG` environment variables set.

Okay, so if you run this script, you can see the output the GPT-3.5 gives.  Well that's nice, but what if we want to save it?  What we want is to do this instead of `!print`:

    !save hod-{puznum}.sql

In addition to `!format` formatting its "verbatim" input, arguments are also automatically formatted.
So where could `puznum` come from?

## context stays available

Now here's where AIPL is different than other array languages.

All the way at the beginning of the script, we had that `!split` which gave us the list of puzzle numbers.
If we change that to this:

    !split>puznum

Then the list of puzzle numbers will be named `puznum`, and be carried forward as additional context to future results.
So even though the puzzle number gets converted to a URL, which gets converted to HTML, then to text, etc, the earlier named contexts are still available for use in formatting.

You can see this if you view the intermediate outputs with `--step rich`:

______

## expensive operations are cached

Note that the second time through, it ran a lot faster!
This is because AIPL automatically caches the results of expensive operations in a sqlite db called `aipl-cache.sqlite`--you can use [VisiData](visidata.org) or another tool to inspect it.
Since the LLM prompt hasn't changed, AIPL uses the previously cached output, to save both time and money.
(Most of the time, in development, you are going to be trying things over and over, so this is a great convenience.
When you want to deliberately not use the cache, you can use the `--no-cache` CLI flag.

## inputs are actually tables

You may have already noticed that the operands actually look like whole *tables*, instead of lists.
This is because under the hood, they are tables.
For purposes of looping like an array language, it's the rightmost or most-recently-added column
which is automatically looped into and over.

But the other columns are still available, and certain operators besides `!format` can take advantage of them.
Like if we put `!json` before the `!save`:

    !json
    !save hod-solutions.json

`!json` converts the entire table to one single JSON blob, including the immediate output, and all previously named columns.

## cross-joining

Okay, so GPT-3.5 isn't so great at solving the puzzle (at least with the prompt we've given it).
Maybe GPT-4 would do better?

In this script, we could manually replace the model, and run it again.  But what if we wanted to run a new prompt with both models and compare the results?  Or on 10 different models?

With the `!cross` operator (and one more language feature), we can.  Let's put this at the top of the script:

    !split>model>>models
    gpt-3.5-turbo
    gpt-4.0

And replace the `!llm` with this:

    !cross <<models
    !llm model={model}

What's happening here?  `!cross` is our first binary operator: it takes **two** inputs, whereas our previous operators are all unary (only taking one input).  `!cross` returns the cross product of these two inputs. This will result in two subtables, each one with one of the models and the prompt.

So we make a new input and use `>>models` to remember the whole table for later.  (`>model` names the column of values, so we can refer to it in arg formatting).

Then we go about our usual business constructing this main table.
Just before running `!llm`, we use `!cross` to do the cross-join, and we use `<<models` to pass the second input.
(We can also use `<<foo` to replace the one input of a unary operator; or we could pass the second input of a binary operator using the "verbatim input", which is not really useful for `!cross`.  But it could be useful for other binary operators.)

## what next?

These are the basics of AIPL; you may want to learn about other available operators, but otherwise you now the fundamental structure that everything fits into.

- If you want to drop into Python, you can either just use `!python` which executes its input, or you can write an operator; it's pretty easy.
:.  See [the docs on Operators](docs/operators.md).



