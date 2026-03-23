# MARPLE

**Mini APL Language Experiment — a first-generation APL interpreter in Python**

I started work on MARPLE for fun. I've wanted to write an APL interpreter, ever since I came across the language in the late 1960s.
MARPLE scratches that itch. It runs on a desktop computer and is designed to be portable to a Raspberry Pi Pico.

MARPLE is incomplete but it's already usable.

It is implemented in Python. Performance is better than you might expect, as it uses numpy arrays under the hood.

It has a simple mechanism that allows you to add new language features in Python and then use i-beams to turn them into functions available to the APL developer.

Claude and Claude code have done all the hard work. Getting to this point has taken a day and a half. I have much more I want to implement, and I expect to do so in days rather than months.

## MARPLE is Alpha code

MARPLE is incomplete; some basic system functions and variables are still missing.

It probably has lots of bugs. Claude code and I have developed it using TDD (Test-Driven Development) but I am certain that bugs will emerge with use.

MARPLE is not, and never will be, a commercial product. It lacks many of the features that make Dyalog APL a compelling proposition for serious APL developers. The size of MARPLE's development and support team lies somewhere between 0 and 1.

But it's been fun and I hope it's useful. Do let me know what you think of it!

## Quick start

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if you don't have it, then:

```bash
uv venv
source .venv/bin/activate      # on Windows: .venv\Scripts\activate
uv pip install marple-lang
marple
```

Or install from source:

```bash
git clone https://github.com/romilly/marple.git
cd marple
uv venv
source .venv/bin/activate      # on Windows: .venv\Scripts\activate
uv pip install -e .
marple
```

```apl
      2 3 4 + 10 20 30
12 23 34
      M ← 3 4⍴⍳12
      (+/⍤1) M
10 26 42
      )off
```

## What's in these docs

| Section | What it's for |
|---------|---------------|
| [Getting Started](getting-started/index.md) | Install MARPLE, launch the REPL, try your first expressions |
| [Tutorials](tutorials/index.md) | Step-by-step lessons for beginners and experienced APL programmers |
| [How-To Guides](how-to/index.md) | Concise recipes for specific tasks |
| [Reference](reference/index.md) | Complete specification of every function, operator, and feature |
| [Explanation](explanation/index.md) | Background, design rationale, and history |
| [Troubleshooting](troubleshooting/index.md) | Error messages, common mistakes, and FAQ |
| [Appendices](appendices/index.md) | Glossary, further reading, changelog |

## Key features

- **Flat arrays** — no nested arrays, no depth, no complexity. Scalars, vectors, matrices, and higher-rank arrays, all rectangular.
- **Rank operator** (`⍤`) — apply any function at any cell rank. The single most important operator missing from first-generation APL, added here because it was designed for flat arrays.
- **From indexing** (`⌷`) — select major cells along the leading axis. Composes with the rank operator for arbitrary-axis selection.
- **Direct definition** — dfns (`{⍺+⍵}`) and dops (`{⍺⍺/⍵}`) with guards, recursion, and lexical scope. No tradfns.
- **Python-powered** — NumPy backend when available (~73× faster for large arrays), pure-Python fallback for portability.
- **40+ primitives** — arithmetic, comparison, boolean, structural, and mixed functions, all with scalar extension.

## Who is this for?

- **APL programmers** curious about a clean-sheet flat-array APL with rank and leading-axis indexing
- **Programmers from other languages** who want to learn array thinking without the complexity of a full commercial APL
- **Educators** looking for a small, self-contained APL that runs anywhere Python does
- **Tinkerers** who want APL on a micro-controller
- **Students** who want to see how to build a simple interpreter and language eco-system
- **AI skeptics** who want to evaluate a substantial body of code build using AI code generation 
