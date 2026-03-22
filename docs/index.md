# MARPLE

**Mini APL Language Experiment — a first-generation APL interpreter in Python**

I started work on MARPLE for fun. I've wanted to write an APL interpreter, ever since I came across the language in the late 1960s.

For many years now I have used Dyalog APL for personal projects, and I love it. It's fast, solid and well-supported. It's also allowed me to learnfrom some very smart people. But for me, it has two disadvantages: I can't extend it, and it uses *floating* nested arrays.

Ken Iverson preferred the *grounded* approach, and so do I. While I have not implemented nested arrays in MARPLE yet, I plan to do so and I will follow the approach described by Iverson in his **Dictionary of APL**.

I've also made MARPLE easy to extend. It is implemented in Python, and there is a simple mechanism that allows you to add new language features in Python and then use i-beams to turn them into functions available to the APL developer.

MARPLE scratches that itch. It runs on desktop Python (with optional NumPy acceleration) and is designed to be portable to CircuitPython on a Raspberry Pi Pico.

Claude and Claude code have done all the hard work. Getting to this point has taken a day and a half. I have much more I want to implement, and I expect to do so in days rather than months.

MARPLE is not, and never will be, a commercial product, and it lacks many of the features that make Dyalog APL a compelling proposition for serious APL developers. But it's been fun and I hope it's useful. Do let me know what you think of it!

## Quick start

MARPLE is not yet on PyPI, so you install it from the GitHub repository:

```bash
git clone https://github.com/romilly/marple.git
cd marple
python -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate
pip install -e .
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
- **Tinkerers** who want APL on a microcontroller

<!-- TODO: Romilly — add anything else about the intended audience or non-goals -->
