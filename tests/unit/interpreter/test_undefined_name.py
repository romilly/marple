"""Undefined names should raise an error, not be silently ignored."""

import pytest

from marple.engine import Interpreter
from marple.errors import APLError


class TestUndefinedNameInDyadicPosition:
    def test_undefined_name_between_args_raises_error(self) -> None:
        interp = Interpreter(io=1)
        with pytest.raises(APLError):
            interp.run("1 0 1 0 0 nosuchfn ⍳5")
