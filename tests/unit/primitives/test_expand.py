"""Expand (\\) tests."""

from marple.numpy_array import APLArray
from marple.engine import Interpreter


class TestExpand:
    def test_expand(self) -> None:
        result = Interpreter(io=1).run("1 0 1 0 1\\1 2 3")
        assert result == APLArray.array([5], [1, 0, 2, 0, 3])
