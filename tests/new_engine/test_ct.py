"""Comparison tolerance tests — new engine."""

from marple.arraymodel import S
from marple.engine import Interpreter


class TestComparisonTolerance:
    def test_equal_within_tolerance(self) -> None:
        i = Interpreter(io=1)
        assert i.run("1=1.0000000000000001") == S(1)

    def test_not_equal_outside_tolerance(self) -> None:
        i = Interpreter(io=1)
        assert i.run("1=1.001") == S(0)

    def test_ct_affects_less_equal(self) -> None:
        i = Interpreter(io=1)
        assert i.run("1≤1.0000000000000001") == S(1)

    def test_ct_zero_strict(self) -> None:
        i = Interpreter(io=1)
        i.run("⎕CT←0")
        # With CT=0, values must be exactly equal
        # 1.00000000000001 is distinguishable from 1.0 in float64
        assert i.run("1=1.00000000000001") == S(0)

    def test_index_of_uses_ct(self) -> None:
        i = Interpreter(io=1)
        assert i.run("1 2 3⍳2.0000000000000001") == S(2)

    def test_membership_uses_ct(self) -> None:
        i = Interpreter(io=1)
        result = i.run("2.0000000000000001∈1 2 3")
        assert result == S(1)
