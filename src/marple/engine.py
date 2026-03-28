"""Class-based APL interpreter for MARPLE."""

from typing import Any

from marple.arraymodel import APLArray, S


class Interpreter:
    def __init__(self, io: int | None = None) -> None:
        from marple.config import get_default_io
        effective_io = io if io is not None else get_default_io()
        self.env: dict[str, Any] = {
            "⎕IO": S(effective_io),
        }
