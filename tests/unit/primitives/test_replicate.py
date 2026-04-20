"""Replicate / Compress (/) tests."""

from marple.ports.array import APLArray
from marple.engine import Interpreter


class TestReplicate:
    def test_compress(self) -> None:
        assert Interpreter(io=1).run("1 0 1 0 1/1 2 3 4 5") == APLArray.array([3], [1, 3, 5])

    def test_replicate(self) -> None:
        assert Interpreter(io=1).run("1 2 3/4 5 6") == APLArray.array([6], [4, 5, 5, 6, 6, 6])

    def test_replicate_scalar_left(self) -> None:
        assert Interpreter(io=1).run("3/1 2 3") == APLArray.array([9], [1, 1, 1, 2, 2, 2, 3, 3, 3])

    def test_replicate_scalar_both(self) -> None:
        assert Interpreter(io=1).run("2/5") == APLArray.array([2], [5, 5])
