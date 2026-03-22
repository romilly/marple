# MARPLE Documentation: Editing Brief

*This brief is for Claude (in chat or Claude Code) working on the MARPLE docs. It explains what exists, what needs filling in, and how to do it well.*

## Context

The `docs/` directory contains 119 Markdown files organised for MkDocs with the Material theme. The `mkdocs.yml` in the repo root defines the navigation. The site builds cleanly. Many pages have substantial content already; others are stubs with headings and TODO comments.

The spec documents in the project files (`MARPLE_Rank_Operator.md`, `MARPLE_Indexing.md`, `MARPLE_Namespaces_And_IBeams.md`, `MARPLE_EA_Brief.md`, `MARPLE_Project_Status.md`) are the authoritative source for MARPLE's design. The interpreter source is under `src/marple/`. The test suite has 290+ tests.

## Priority order

### 1. Verify all existing examples against the REPL

Every code block tagged `apl` should be tested by running the expressions in MARPLE and confirming the output matches. Fix any discrepancies. This is the single most important task — wrong examples in tutorials destroy trust.

How: launch `marple` (or use the interpreter programmatically), run each expression, capture output, compare with what's in the docs.

### 2. Fill in reference pages

These are the pages people search for. Generate from the interpreter source and spec documents.

- **`reference/primitives/arithmetic.md`** — for each of `+ - × ÷ ⌈ ⌊ * ⍟ | ! ○`: glyph, name, monadic form (signature, description, 2-3 examples), dyadic form (signature, description, 2-3 examples), edge cases. Use a consistent format across all entries.
- **`reference/primitives/structural.md`** — same treatment for `⍴ ⍳ , ⌽ ⊖ ⍉ ↑ ↓ ∈ ⍋ ⍒`.
- **`reference/primitives/mixed.md`** — same for `⊤ ⊥ ⌹ ⍎ ⍕ ⌷`.
- **`reference/primitives/comparison.md`** and **`boolean.md`** — expand the existing tables with examples.
- **`reference/glyph-input.md`** — generate the complete backtick→glyph table from `src/marple/glyphs.py`.
- **`reference/error-messages.md`** — confirm the complete list of error codes from the interpreter source.
- **`reference/system/system-variables.md`** — confirm which `⎕` variables are implemented and their defaults.
- **`reference/system/system-commands.md`** — verify against `repl.py`.

### 3. Fill in worked examples

These need to be built interactively with the REPL to ensure correctness.

- **`tutorials/worked-examples/csv-pipeline.md`** — read a CSV, split with `v2m`, extract columns with From+Rank, reduce for summaries.
- **`tutorials/worked-examples/statistics.md`** — mean, variance, stddev, correlation as dfns.
- **`tutorials/worked-examples/text-processing.md`** — word count, search, case conversion.
- **`tutorials/worked-examples/matrix-maths.md`** — solve linear equations with `⌹`.
- **`tutorials/worked-examples/game-of-life.md`** — classic APL demo, step by step.

### 4. Expand migration guides

- **`tutorials/for-aplers/from-j.md`** — fill in the comparison table and expand discussion of tacit vs dfn style, boxing differences, glyph mappings.
- **`tutorials/for-aplers/from-gnu-apl.md`** — expand comparison, especially around tradfns→dfns migration and the absence of nested arrays.

### 5. Fill in remaining stubs

Look for `<!-- TODO -->` comments throughout the docs. Most are small: confirm a behaviour, add an example, expand a table. Address them file by file.

## Style guide

### Tone
- Warm but concise. Not chatty, not dry.
- Address the reader as "you". Don't say "the user".
- Use "MARPLE" not "the MARPLE interpreter" unless disambiguation is needed.

### Code examples
- Use the `apl` language tag for APL code blocks.
- Show the six-space REPL prompt for interactive examples.
- Show output left-aligned (no prompt) on the line after the expression.
- Add a `⍝` comment on the expression line when the purpose isn't obvious.
- Keep examples short — 1-5 lines each. Longer examples belong in worked examples.

### Structure
- Every page starts with a level-1 heading matching the nav title.
- Use MkDocs admonitions (`!!! note`, `!!! tip`, `!!! warning`) sparingly — one or two per page maximum.
- End tutorial pages with "Key points" (short bulleted summary) and a "Next:" link.
- End how-to pages with a "See also:" link to the relevant tutorial or reference page.
- Reference pages should be terse and complete. Don't explain *why* — that's for the Explanation section.

### What NOT to include
- Implementation details (Python internals, module structure, parser mechanics) — those belong in the spec documents, not user docs.
- Speculative future features — only document what's implemented. Mention planned features briefly with "planned for a future version" if relevant.
- Comparisons that disparage other APLs — MARPLE makes different choices, not better ones.

## Pages that need Romilly's input

These are marked with `<!-- TODO: Romilly -->` and should be left as stubs or drafted for review:

- **`docs/index.md`** — the opening paragraph (elevator pitch, personal voice)
- **`explanation/why-marple.md`** — design motivation, personal story, manifesto
- **`appendices/contributing.md`** — contribution process, code of conduct
- **`getting-started/installation.md`** — confirm exact install commands and PyPI status
- **`getting-started/repl.md`** — confirm which terminals are tested
- **`explanation/python-connection.md`** — Pico status update
- **`troubleshooting/faq.md`** — Pico status update
