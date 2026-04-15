"""Tokens and Tokenizer for marple.

Value-producing tokens (numbers, strings, identifiers, function
glyphs, omega/alpha, etc.) are emitted as AST nodes directly — a
`NumberToken` doesn't exist; the tokenizer produces `Num` nodes
straight out. This collapses what used to be two parallel type
hierarchies (Token classes mirrored by AST node classes) into one.

Marker tokens (parens, diamonds, braces, brackets, etc.) and the
`OperatorToken` (deferred because of axis-spec parsing) remain as
`Token` subclasses, sitting alongside AST nodes in the token list.

The token list produced by `tokenize()` is a heterogeneous
`list[Token | Executable]`.
"""

import re
from dataclasses import dataclass
from typing import cast

from marple.nodes import (
    Alpha,
    AlphaAlpha,
    Executable,
    Nabla,
    Num,
    Omega,
    OmegaOmega,
    PrimitiveFunction,
    QualifiedVar,
    Str,
    SysFunc,
    SysVar,
    Var,
    Zilde,
)


def _isdigit(ch: 'str | None') -> bool:
    return ch is not None and "0" <= ch <= "9"

def _isalpha(ch: 'str | None') -> bool:
    return ch is not None and (("a" <= ch <= "z") or ("A" <= ch <= "Z") or ch in "∆⍙")

def _isalnum(ch: 'str | None') -> bool:
    return _isdigit(ch) or _isalpha(ch)


@dataclass
class Token:
    """Base for marker tokens (parens, delimiters) and the operator
    token. Value-producing lexical units are emitted as AST nodes,
    not Tokens."""


# ── Operator token (deferred: axis-spec parsing lives in parser) ──

@dataclass
class OperatorToken(Token):
    glyph: str


# ── Marker tokens ──

@dataclass
class LParenToken(Token): pass
@dataclass
class RParenToken(Token): pass
@dataclass
class AssignToken(Token): pass
@dataclass
class DiamondToken(Token): pass
@dataclass
class LBraceToken(Token): pass
@dataclass
class RBraceToken(Token): pass
@dataclass
class GuardToken(Token): pass
@dataclass
class LBracketToken(Token): pass
@dataclass
class RBracketToken(Token): pass
@dataclass
class SemicolonToken(Token): pass
@dataclass
class EofToken(Token): pass


FUNCTION_GLYPHS = set("!+-×÷⌈⌊*⍟|<≤=≥>≠∧∨~⍴⍳,↑↓⌽⊖⍉⍋⍒⊤⊥⍎⍕⌹○⌷≡≢∈?")

# System functions are classified as verbs; everything else starting
# with ⎕ is a system variable. Lives here because the distinction is
# lexical — the tokenizer emits the right AST node directly.
_SYS_FUNCTIONS = frozenset({
    "⎕CR", "⎕FX", "⎕NC", "⎕EX", "⎕SIGNAL", "⎕EA",
    "⎕UCS", "⎕DR", "⎕NREAD", "⎕NWRITE", "⎕NEXISTS", "⎕NDELETE",
    "⎕DL", "⎕FMT", "⎕VFI", "⎕JSON", "⎕NL", "⎕CSV",
})


SINGLE_CHAR_TOKENS: dict[str, 'Token | Executable'] = {
    "(": LParenToken(),
    ")": RParenToken(),
    "←": AssignToken(),
    "⋄": DiamondToken(),
    "/": OperatorToken("/"),
    "⌿": OperatorToken("⌿"),
    "\\": OperatorToken("\\"),
    "⍀": OperatorToken("⍀"),
    ".": OperatorToken("."),
    "∘": OperatorToken("∘"),
    "⍤": OperatorToken("⍤"),
    "⍣": OperatorToken("⍣"),
    "⌶": OperatorToken("⌶"),
    "⍨": OperatorToken("⍨"),
    "{": LBraceToken(),
    "}": RBraceToken(),
    "⍵": Omega(),
    "⍺": Alpha(),
    "∇": Nabla(),
    ":": GuardToken(),
    "[": LBracketToken(),
    "]": RBracketToken(),
    ";": SemicolonToken(),
    "⍬": Zilde(),
}


class Tokenizer:
    _NUM_RE = re.compile(r'\d+(?:\.\d*)?(?:[eE][¯\-+]?\d+)?')

    def __init__(self, source: str) -> None:
        # `_text` is the raw source, used for regex matching
        # (`_read_number`). `_source` is the same chars as a list
        # with two `None` sentinels appended, so single-char reads
        # at `_pos`, `_pos+1`, `_pos+2` are always in-range and
        # return `None` past end-of-input.
        self._text = source
        self._source: list[str | None] = list(source) + [None, None]
        self._pos = 0

    def _current(self) -> str | None:
        return self._source[self._pos]

    def _advance(self) -> None:
        self._pos += 1

    def _skip_whitespace(self) -> None:
        while self._current() in (" ", "\t", "\r", "\n"):
            self._advance()

    def _read_number(self) -> Num:
        """Consume a numeric literal via regex; let int()/float() parse.
        Callers guarantee `_pos` is on a digit, so the match always succeeds.
        """
        m = cast(re.Match[str], self._NUM_RE.match(self._text, self._pos))
        self._pos = m.end()
        text = m.group().replace("¯", "-")
        try:
            return Num(int(text))
        except ValueError:
            return Num(float(text))

    def _read_string(self) -> Str:
        self._advance()  # skip opening quote
        result = ""
        # Explicit None check needed: without it, an unterminated
        # string would advance past the sentinel zone and raise
        # IndexError.
        while self._current() not in ("'", None):
            result += self._current()  # type: ignore[operator]
            self._advance()
        if self._current() == "'":
            self._advance()  # skip closing quote
        return Str(result)

    def _read_id(self) -> Var | QualifiedVar:
        result = ""
        while _isalnum(self._current()) or self._current() == "_":
            result += self._current()  # type: ignore[operator]
            self._advance()
        # Check for :: (qualified name) — sentinels make the
        # `_pos+1` / `_pos+2` reads safe without bounds checks.
        if (
            self._current() == ":"
            and self._source[self._pos + 1] == ":"
            and (_isalpha(self._source[self._pos + 2]) or self._source[self._pos + 2] == "_")
        ):
            result += "::"
            self._advance()  # skip first :
            self._advance()  # skip second :
            rest = self._read_id()
            rest_name = rest.name if isinstance(rest, Var) else "::".join(rest.parts)
            return QualifiedVar((result + rest_name).split("::"))
        return Var(result)

    def tokenize(self) -> list[Token | Executable]:
        tokens: list[Token | Executable] = []
        while self._current() is not None:
            self._skip_whitespace()
            ch = self._current()
            if ch is None:
                break
            if ch == "⍝":
                break
            if ch == "'":
                tokens.append(self._read_string())
            elif ch == "⍞":
                tokens.append(SysVar("⍞"))
                self._advance()
            elif ch == "⎕":
                self._advance()
                name = ""
                while _isalpha(self._current()):
                    name += self._current()  # type: ignore[operator]
                    self._advance()
                full = "⎕" + name.upper()
                tokens.append(SysFunc(full) if full in _SYS_FUNCTIONS else SysVar(full))
            elif ch == "¯":
                self._advance()
                if not _isdigit(self._current()):
                    from marple.errors import SyntaxError_
                    raise SyntaxError_("High minus ¯ must be followed by a digit")
                num_node = self._read_number()
                tokens.append(Num(-num_node.value))
            elif _isdigit(ch):
                tokens.append(self._read_number())
            elif ch in FUNCTION_GLYPHS:
                tokens.append(PrimitiveFunction(ch))
                self._advance()
            elif ch == "⍺" and self._source[self._pos + 1] == "⍺":
                tokens.append(AlphaAlpha())
                self._advance()
                self._advance()
            elif ch == "⍵" and self._source[self._pos + 1] == "⍵":
                tokens.append(OmegaOmega())
                self._advance()
                self._advance()
            elif ch in SINGLE_CHAR_TOKENS:
                tokens.append(SINGLE_CHAR_TOKENS[ch])
                self._advance()
            elif ch == "$" and self._source[self._pos + 1] == ":" and self._source[self._pos + 2] == ":":
                self._advance()  # skip $
                self._advance()  # skip first :
                self._advance()  # skip second :
                rest = self._read_id()
                rest_name = rest.name if isinstance(rest, Var) else "::".join(rest.parts)
                tokens.append(QualifiedVar(("$::" + rest_name).split("::")))
            elif _isalpha(ch) or ch == "_":
                tokens.append(self._read_id())
            else:
                # Defensive: any character that reached this point is
                # unrecognised. The previous behaviour (`self._advance()`)
                # silently dropped the char, which masked two real bugs
                # discovered on 2026-04-09 — the missing zilde literal
                # (⍬) and the missing commute operator (⍨), both of
                # which were silently swallowed and produced confusing
                # downstream errors. Raising here surfaces the same
                # class of bug immediately and clearly.
                from marple.errors import SyntaxError_
                raise SyntaxError_(f"Unknown character: {ch!r}")
        tokens.append(EofToken())
        return tokens
