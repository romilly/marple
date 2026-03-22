from __future__ import annotations

# Backtick prefix map: `x → APL glyph
# Layout follows Dyalog's backtick keyboard where possible
GLYPH_MAP: dict[str, str] = {
    # Arithmetic
    "-": "×",
    "=": "÷",
    # Comparison
    "<": "≤",
    ">": "≥",
    "/": "≠",
    # Structural
    "r": "⍴",
    "i": "⍳",
    "e": "∈",
    "t": "↑",
    "y": "↓",
    "q": "⌽",
    "Q": "⍉",
    # Grade
    "g": "⍋",
    "G": "⍒",
    # Logic
    "^": "∧",
    "v": "∨",
    "~": "⍲",
    "T": "⍱",
    # Math
    "*": "⍟",
    "o": "○",
    "!": "⌈",
    "d": "⌊",
    "D": "⌹",
    "p": "⌈",
    "b": "⌊",
    # Encode/decode
    "n": "⊤",
    "N": "⊥",
    # I/O and special
    "w": "⍵",
    "a": "⍺",
    "V": "∇",
    "l": "←",
    "x": "⋄",
    "z": "⍎",
    "Z": "⍕",
    # Jot, compose, rank, from
    "j": "∘",
    "J": "⍤",
    "I": "⌷",
    # High minus
    "2": "¯",
    # Comment
    "c": "⍝",
    # Braces (convenience)
    "[": "{",
    "]": "}",
}


def expand_glyphs(line: str) -> str:
    """Replace backtick sequences with APL glyphs.

    `x → APL glyph, `` → literal backtick.
    """
    result: list[str] = []
    i = 0
    while i < len(line):
        if line[i] == "`" and i + 1 < len(line):
            next_ch = line[i + 1]
            if next_ch == "`":
                result.append("`")
                i += 2
            elif next_ch in GLYPH_MAP:
                result.append(GLYPH_MAP[next_ch])
                i += 2
            else:
                result.append("`")
                i += 1
        else:
            result.append(line[i])
            i += 1
    return "".join(result)
