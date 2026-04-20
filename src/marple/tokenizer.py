"""Tokens and Tokenizer for marple.

Value-producing tokens (numbers, strings, identifiers, function
glyphs, omega/alpha, etc.) are emitted as AST nodes directly — a
`NumberToken` doesn't exist; the tokenizer produces `Num` nodes
straight out. This collapses what used to be two parallel type
hierarchies (Token classes mirrored by AST node classes) into one.

Marker tokens (parens, diamonds, braces, brackets, etc.) and the
`OperatorToken` (deferred because of axis-spec parsing) remain as
`Token` subclasses, sitting alongside AST nodes in the token list.

`Token` inherits from `Node` so the token list is `list[Node]`
— tokens and AST nodes share the "parser-stack item" contract.
"""

import re
from typing import Any, Callable, cast

from marple.executor import (
    Alpha,
    AlphaAlpha,
    Nabla,
    Node,
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


def _isdigit(ch: str | None) -> bool:
    return ch is not None and "0" <= ch <= "9"

def _isalpha(ch: str | None) -> bool:
    return ch is not None and (("a" <= ch <= "z") or ("A" <= ch <= "Z") or ch in "∆⍙")

def _isalnum(ch: str | None) -> bool:
    return _isdigit(ch) or _isalpha(ch)


class Token(Node):
    """Base for marker tokens (parens, delimiters) and the operator
    token. Value-producing lexical units are emitted as AST nodes,
    not Tokens.

    Inherits from `Node` so the token list is `list[Node]` —
    tokens ARE parser-stack items, same as AST nodes. Node's
    `__dict__`-based `__eq__` means two marker-token instances with
    no fields compare equal; OperatorToken's glyph field differentiates.
    """


# ── Operator token (deferred: axis-spec parsing lives in parser) ──

class OperatorToken(Token):
    def __init__(self, glyph: str) -> None:
        self.glyph = glyph


# ── Marker tokens ──

class LParenToken(Token): pass
class RParenToken(Token): pass
class AssignToken(Token): pass
class DiamondToken(Token): pass
class LBraceToken(Token): pass
class RBraceToken(Token): pass
class GuardToken(Token): pass
class LBracketToken(Token): pass
class RBracketToken(Token): pass
class SemicolonToken(Token): pass
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


SINGLE_CHAR_TOKENS: dict[str, Node] = {
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
    "∇": Nabla(),
    ":": GuardToken(),
    "[": LBracketToken(),
    "]": RBracketToken(),
    ";": SemicolonToken(),
    "⍬": Zilde(),
}


class Tokenizer:
    _NUM_RE = re.compile(r'\d+(?:\.\d*)?(?:[eE][¯\-+]?\d+)?')
    _ID_RE = re.compile(r'[a-zA-Z_∆⍙][a-zA-Z0-9_∆⍙]*(?:::[a-zA-Z_∆⍙][a-zA-Z0-9_∆⍙]*)*')

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

    def _peek(self, offset: int = 1) -> str | None:
        """Look ahead `offset` characters. Sentinels make offsets
        1 and 2 always safe."""
        return self._source[self._pos + offset]

    def _advance(self) -> None:
        self._pos += 1

    def _skip_whitespace(self) -> None:
        while self._current() in (" ", "\t", "\r", "\n"):
            self._advance()

    def _read_number(self) -> Num:
        """Consume a numeric literal via regex; let int()/float() parse.
        Callers guarantee `_pos` is on a digit, so the match always succeeds.
        """
        # cast(Any, …) rather than cast(re.Match[str], …): MicroPython's
        # re module doesn't expose the Match class, and cast's first arg
        # is evaluated at call time. group(0) explicit because
        # MicroPython requires the group number.
        m = cast(Any, self._NUM_RE.match(self._text, self._pos))
        self._pos = m.end()
        text = m.group(0).replace("¯", "-")
        try:
            return Num(int(text))
        except ValueError:
            return Num(float(text))

    def _read_string(self) -> Str:
        self._advance()  # skip opening quote
        end = self._text.find("'", self._pos)
        if end == -1:
            from marple.errors import SyntaxError_
            raise SyntaxError_("Unterminated string literal")
        result = self._text[self._pos:end]
        self._pos = end + 1  # skip past closing quote
        return Str(result)

    def _read_id(self) -> Var | QualifiedVar:
        """Consume an identifier, possibly qualified (`a::b::c`).
        Callers guarantee `_pos` is on an id-start char, so the
        match always succeeds.
        """
        m = cast(Any, self._ID_RE.match(self._text, self._pos))
        self._pos = m.end()
        text = m.group(0)
        return QualifiedVar(text.split("::")) if "::" in text else Var(text)

    def tokenize(self) -> list[Node]:
        tokens: list[Node] = []
        while True:
            self._skip_whitespace()
            ch = self._current()
            if ch is None or ch == "⍝":
                break
            tokens.append(self._next_token(ch))
        tokens.append(EofToken())
        return tokens

    def _next_token(self, ch: str) -> Node:
        handler = self._HANDLERS.get(ch)
        if handler:
            return handler(self)
        if _isdigit(ch):
            return self._read_number()
        if ch in FUNCTION_GLYPHS:
            self._advance()
            return PrimitiveFunction(ch)
        if ch in SINGLE_CHAR_TOKENS:
            self._advance()
            return SINGLE_CHAR_TOKENS[ch]
        if _isalpha(ch) or ch == "_":
            return self._read_id()
        from marple.errors import SyntaxError_
        raise SyntaxError_(f"Unknown character: {ch!r}")

    def _read_quote_quad(self) -> Node:
        self._advance()
        return SysVar("⍞")

    def _read_quad(self) -> Node:
        self._advance()
        name = ""
        while _isalpha(self._current()):
            name += self._current()  # type: ignore[operator]
            self._advance()
        full = "⎕" + name.upper()
        return SysFunc(full) if full in _SYS_FUNCTIONS else SysVar(full)

    def _read_high_minus(self) -> Node:
        self._advance()
        if not _isdigit(self._current()):
            from marple.errors import SyntaxError_
            raise SyntaxError_("High minus ¯ must be followed by a digit")
        num_node = self._read_number()
        return Num(-num_node.value)

    def _read_alpha(self) -> Node:
        if self._peek() == "⍺":
            self._advance()
            self._advance()
            return AlphaAlpha()
        self._advance()
        return Alpha()

    def _read_omega(self) -> Node:
        if self._peek() == "⍵":
            self._advance()
            self._advance()
            return OmegaOmega()
        self._advance()
        return Omega()

    def _read_workspace_qualified(self) -> Node:
        if not (self._peek() == ":" and self._peek(2) == ":"):
            from marple.errors import SyntaxError_
            raise SyntaxError_("Unknown character: '$'")
        self._advance()  # skip $
        self._advance()  # skip first :
        self._advance()  # skip second :
        rest = self._read_id()
        rest_name = rest.name if isinstance(rest, Var) else "::".join(rest.parts)
        return QualifiedVar(("$::" + rest_name).split("::"))

    _HANDLERS: dict[str, Callable[['Tokenizer'], Node]] = {
        "'": _read_string,
        "⍞": _read_quote_quad,
        "⎕": _read_quad,
        "¯": _read_high_minus,
        "⍺": _read_alpha,
        "⍵": _read_omega,
        "$": _read_workspace_qualified,
    }
