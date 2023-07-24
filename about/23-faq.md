# FAQ

## Q: why would I not just write some code?

First of all, AIPL is code.  In fact it's entirely based on Python, and allows you to start writing code by using the `!python` operator.
However, there are reasons why you might not want to just write Python code in the first place.

The biggest being: you shouldn't over-engineer prototypes.

Yes, if you were going to put some AI workflow into production, for "real" users, you would probably want to write some "real" code!
You might need to consider factors like implementing real-time responses, handling large data volumes, or incorporating custom code within a loop. But that's going to cost real time, real money, and real skill.

Before reaching that stage, you need to know how your idea can be done with AI in its current form.
You may need to explore which of the available models might be better or cheaper, figure out how exactly you would have to organize the pipeline so that you can get the results you need, and engineer the literal prompts themselves.
You might even have to scrap the idea altogether if you can't get GPT (or whatever LLM) to respond accurately--and if that's the case, you want to find that out quickly, before investing any real resources.

You want something quick-and-dirty to experiment with. You want to be able to whip up a prototype in a couple hours.

But you need something bigger than prompting directly to ChatGPT within the browser. It's fine for testing one thing, and you can do the pre- and post-processing yourself by hand.  For anything greater than N=1, though, you're already wanting something more reproducible.

For instance, here's a script to summarize any number of webpages: https://github.com/saulpw/aipl/blob/develop/examples/summarize.aipl

To do this in Python would involve being explicit about iteration, caching, error-handling, and the result would be a more unwieldy script, with the requisite quoting and/or escaping, code out-of-order and perhaps code scattered across multiple files, even the boilerplate--these things add friction for someone who knows Python, and make it impossible for a non-coder.

At the tiny sets (N=10 or N=100) we use to validate our ideas, we want our focus to be on the experiments themselves as much as possible.

There's a progression of computational tools: from calculators, to spreadsheets, to notebooks, to scripts, to programs, to systems.  Each level gives you more power and flexibility, but requires more attention and skill.

In this context, ChatGPT is only a calculator, while Python is used to create programs and systems. Python notebooks are useful but have their quirks, and don't scale well without explicit adjustments.

AIPL fills the gap between notebooks and programs, functioning as a platform for scripts. Scripts are less flexible than full programs but are easier to write, modify, and maintain. They are self-contained in a single text file, making them easy to share and understand. AIPL scripts provide a clear flow of operations and include required content inline.

It's like asking, why would I write a bash script, why would I not just write some code?  And sure!  You might want to do that.  But maybe you start with `cut | sort | uniq | sort -n` and see if that gets the job done in a fraction of the time.

## Q: What about the name "AIPL"?

"AIPL" pays homage to APL, the original array language by Ken Iverson in the 1960s, which inspired some [core design decisions in AIPL](../23-design.md).
Though AIPL is a generic pipeline language and not at all limited to AI, its first use case was for LLM experiments, and some features (like inline prompts) are particularly useful in the LLM world.
Also when GPT-4 suggested "Array-Inspired Pipeline Language" (I fed it the README and asked for a list of 5 backronyms), it pretty much nailed it, and that sealed the deal.

## Q: What's the basic concept of AIPL?

AIPL is "just" a thin layer over Python, offering various operators for data processing and calling LLMs. New operators are regularly added. Users can even create their own commands using a function decorator (@defop(...)).

The role of AIPL is to execute these Python code snippets consistently across all data in predictable ways. It handles input, output, caching, logging, error handling, and the parallelism. And it turns out that infrastructure is 90% of the work of building a pipeline.

Users are then able to focus on the literal essence of their work: finding the data, arranging the appropriate operators in the correct order with appropriate parameters and prompts. We'll take care of the rest.

AIPL can be used for prototypes up to about a million rows, and the resulting .aipl script is the ultimate reference of the 'secret sauce'.

Then if/when the need arises for scaling or for a real-time usage pattern, converting the AIPL prototype into a "real" pipeline requires less effort than it would have taken to develop the initial implementation. It is a low-risk process, especially if users write their own runner in Python using another library. [porting cookbooks for $]
