from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    NUMBER = auto()
    FUNCTION = auto()
    LPAREN = auto()
    RPAREN = auto()
    ASSIGN = auto()
    DIAMOND = auto()
    STRING = auto()
    OPERATOR = auto()
    LBRACE = auto()
    RBRACE = auto()
    OMEGA = auto()
    ALPHA = auto()
    NABLA = auto()
    GUARD = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    SEMICOLON = auto()
    SYSVAR = auto()
    QUALIFIED_NAME = auto()
    ID = auto()
    EOF = auto()


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: object


FUNCTION_GLYPHS = set("+-×÷⌈⌊*⍟|<≤=≥>≠∧∨~⍴⍳,↑↓⌽⍉⍋⍒⊤⊥⍎⍕⌹○⌷≡≢∈")

SINGLE_CHAR_TOKENS: dict[str, Token] = {
    "(": Token(TokenType.LPAREN, "("),
    ")": Token(TokenType.RPAREN, ")"),
    "←": Token(TokenType.ASSIGN, "←"),
    "⋄": Token(TokenType.DIAMOND, "⋄"),
    "/": Token(TokenType.OPERATOR, "/"),
    "\\": Token(TokenType.OPERATOR, "\\"),
    ".": Token(TokenType.OPERATOR, "."),
    "∘": Token(TokenType.OPERATOR, "∘"),
    "⍤": Token(TokenType.OPERATOR, "⍤"),
    "⌶": Token(TokenType.OPERATOR, "⌶"),
    "{": Token(TokenType.LBRACE, "{"),
    "}": Token(TokenType.RBRACE, "}"),
    "⍵": Token(TokenType.OMEGA, "⍵"),
    "⍺": Token(TokenType.ALPHA, "⍺"),
    "∇": Token(TokenType.NABLA, "∇"),
    ":": Token(TokenType.GUARD, ":"),
    "[": Token(TokenType.LBRACKET, "["),
    "]": Token(TokenType.RBRACKET, "]"),
    ";": Token(TokenType.SEMICOLON, ";"),
}


class Tokenizer:
    def __init__(self, source: str) -> None:
        self._source = source
        self._pos = 0

    def _current(self) -> str | None:
        if self._pos >= len(self._source):
            return None
        return self._source[self._pos]

    def _advance(self) -> None:
        self._pos += 1

    def _skip_whitespace(self) -> None:
        while self._current() is not None and self._current() == " ":
            self._advance()

    def _read_number(self) -> Token:
        result = ""
        has_dot = False
        while self._current() is not None and (self._current().isdigit() or self._current() == "."):  # type: ignore[union-attr]
            if self._current() == ".":
                if has_dot:
                    break
                has_dot = True
            result += self._current()  # type: ignore[operator]
            self._advance()
        # Handle scientific notation: 1e10, 1E-14, 1.5e3
        if self._current() is not None and self._current() in ("e", "E"):
            result += self._current()  # type: ignore[operator]
            self._advance()
            if self._current() is not None and self._current() in ("-", "+"):
                result += self._current()  # type: ignore[operator]
                self._advance()
            while self._current() is not None and self._current().isdigit():  # type: ignore[union-attr]
                result += self._current()  # type: ignore[operator]
                self._advance()
            return Token(TokenType.NUMBER, float(result))
        value: int | float = float(result) if has_dot else int(result)
        return Token(TokenType.NUMBER, value)

    def _read_string(self) -> Token:
        self._advance()  # skip opening quote
        result = ""
        while self._current() is not None and self._current() != "'":
            result += self._current()  # type: ignore[operator]
            self._advance()
        if self._current() == "'":
            self._advance()  # skip closing quote
        return Token(TokenType.STRING, result)

    def _read_id(self) -> Token:
        result = ""
        while self._current() is not None and (self._current().isalnum() or self._current() == "_"):  # type: ignore[union-attr]
            result += self._current()  # type: ignore[operator]
            self._advance()
        # Check for :: (qualified name)
        if (
            self._current() == ":"
            and self._pos + 1 < len(self._source)
            and self._source[self._pos + 1] == ":"
            and self._pos + 2 < len(self._source)
            and (self._source[self._pos + 2].isalpha() or self._source[self._pos + 2] == "_")
        ):
            result += "::"
            self._advance()  # skip first :
            self._advance()  # skip second :
            rest = self._read_id()
            return Token(TokenType.QUALIFIED_NAME, result + str(rest.value))
        return Token(TokenType.ID, result)

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        while self._current() is not None:
            self._skip_whitespace()
            ch = self._current()
            if ch is None:
                break
            if ch == "⍝":
                break
            if ch == "'":
                tokens.append(self._read_string())
            elif ch == "⎕":
                self._advance()
                name = ""
                while self._current() is not None and self._current().isalpha():  # type: ignore[union-attr]
                    name += self._current()  # type: ignore[operator]
                    self._advance()
                tokens.append(Token(TokenType.SYSVAR, "⎕" + name))
            elif ch == "¯":
                self._advance()
                num_token = self._read_number()
                value = num_token.value
                assert isinstance(value, (int, float))
                tokens.append(Token(TokenType.NUMBER, -value))
            elif ch.isdigit():
                tokens.append(self._read_number())
            elif ch in FUNCTION_GLYPHS:
                tokens.append(Token(TokenType.FUNCTION, ch))
                self._advance()
            elif ch in SINGLE_CHAR_TOKENS:
                tokens.append(SINGLE_CHAR_TOKENS[ch])
                self._advance()
            elif ch == "$" and self._pos + 2 < len(self._source) and self._source[self._pos + 1] == ":" and self._source[self._pos + 2] == ":":
                self._advance()  # skip $
                self._advance()  # skip first :
                self._advance()  # skip second :
                rest = self._read_id()
                tokens.append(Token(TokenType.QUALIFIED_NAME, "$::" + str(rest.value)))
            elif ch.isalpha() or ch == "_":
                tokens.append(self._read_id())
            else:
                self._advance()
        tokens.append(Token(TokenType.EOF, None))
        return tokens
