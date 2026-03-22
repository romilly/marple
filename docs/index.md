# MARPLE

**Mini APL Language Experiment — a first-generation APL interpreter in Python**

<!-- TODO: Romilly — write a paragraph or two in your own voice about what MARPLE is
     and why you built it. The tone should be welcoming but honest: this is a working
     interpreter, not a toy, but it's also a personal project with a point of view. -->

MARPLE is an APL interpreter that implements flat arrays, direct definition (dfns and dops), the rank operator, and From indexing. It follows Iverson's *Dictionary of APL* philosophy rather than APL2's nested model. It runs on desktop Python (with optional NumPy acceleration) and is designed to be portable to CircuitPython on a Raspberry Pi Pico.

## Quick start

```bash
pip install marple
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
