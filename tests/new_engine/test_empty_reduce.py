"""Identity elements for reduce on empty arrays."""

import math

from marple.numpy_array import S
from marple.engine import Interpreter


class TestEmptyReduce:
    def test_plus(self) -> None:
        assert Interpreter(io=1).run("+/⍳0") == S(0)

    def test_minus(self) -> None:
        assert Interpreter(io=1).run("-/⍳0") == S(0)

    def test_times(self) -> None:
        assert Interpreter(io=1).run("×/⍳0") == S(1)

    def test_divide(self) -> None:
        assert Interpreter(io=1).run("÷/⍳0") == S(1)

    def test_max(self) -> None:
        result = Interpreter(io=1).run("⌈/⍳0")
        assert result.data[0] == float("-inf")

    def test_min(self) -> None:
        result = Interpreter(io=1).run("⌊/⍳0")
        assert result.data[0] == float("inf")

    def test_and(self) -> None:
        assert Interpreter(io=1).run("∧/⍳0") == S(1)

    def test_or(self) -> None:
        assert Interpreter(io=1).run("∨/⍳0") == S(0)

    def test_equal(self) -> None:
        assert Interpreter(io=1).run("=/⍳0") == S(1)

    def test_not_equal(self) -> None:
        assert Interpreter(io=1).run("≠/⍳0") == S(0)
