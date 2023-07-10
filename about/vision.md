
# A Toolmaker's Vision

With a simple framework, a common connection interface, and the right set of components, the work becomes relatively easy:

    - the work being done is only the *essence* of the work to be done
       - no unnecessary complexity
       - no impedance mismatch between components

    - the work is more than easy--it is delightful
       - some of this is just raw "oh thank god yes this is what software should be like"
       - some is a surprising depth, an invitation to explore that will often be rewarded
       - some is a nostalgic [feeling of the computer](bluebird.sh/feeling)

    - the work is so easy and delightful that it becomes playful.

Not just can more work get done faster, but a *whole new level* of possibility opens up.

Like the piano, or the typewriter, or the spreadsheet.

## The ladder of computing

The progression of computational tools goes from calculators, to spreadsheets, to notebooks, to scripts, to programs, to systems.
Each level gives you more power and flexibility, and also needs more mana and a higher skill level to use.
The lower you go, the more it's geared towards an individual user; the higher you go, the more towards users operating as part of a larger organization.

In the realm of AI, ChatGPT is a calculator: you can run only 1 calculation at a time.
If you have a one-off question for GPT, you can just open the website and type it in, and they handle some niceties for you.

But if you keep coming back and pasting in a prompt, or you want to run the same prompt with madlibs or a mail merge or across a range of temperatures, or you have to fetch a page from the web, or you have to split the text up so it fits in the context window...you're going to want to use the API (or maybe another LLM).

But you have to write code to use the API.  If your use case is very simple or prescribed, someone may have written the code such that you can use it as an existing program or service.  But for anything requiring even a bit of customization outside of that, you would have to at least use a notebook (which aren't pure text and can be unwieldy), or graduate to a script.

Python has grown into a huge language, and is no longer at the 'script' level for data processing tasks (though it is easier than doing it in Rust!).  Even if the libraries to do what you want already exist, you still need a fair amount of programming experience and skill to make it happen.

AIPL is intended to be at the script level for data processing and AI.
