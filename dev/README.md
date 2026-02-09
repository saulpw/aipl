# dev/

Design documents and historical notes for AIPL development.

## Files

- **[DESIGN.md](DESIGN.md)** -- Main design document. History, motivation, language design choices (data model, rank system, operator taxonomy, the prompt, caching, column naming), architecture evolution across three versions, design decisions, future ideas, and references.

- **[array-notes.md](array-notes.md)** -- Research notes on APL/K array semantics that informed AIPL's rank and nesting model. Covers enclose/disclose, nested vs flat array theory, K language comparisons, and the unimplemented `!defpy` inline Python idea.

- **[v2-unix-experiment.md](v2-unix-experiment.md)** -- Documentation of the June 2024 experiment rewriting AIPL as a Unix pipeline tool (`aid`). Covers the architecture, type-driven dispatch, LastAttrDict, field routing, and an honest assessment of what worked vs what was lost compared to the DSL approach.
