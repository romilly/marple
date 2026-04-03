"""Comparison tolerance tests — new engine."""

from marple.arraymodel import APLArray, S
from marple.engine import Interpreter


class TestComparisonTolerance:
    def test_default_ct(self) -> None:
        assert Interpreter(io=1).run("⎕CT") == S(1e-14)

    def test_equal_within_tolerance(self) -> None:
        assert Interpreter(io=1).run("1=1.0000000000000001") == S(1)

    def test_near_equal(self) -> None:
        assert Interpreter(io=1).run("1=(1÷3)×3") == S(1)

    def test_far_not_equal(self) -> None:
        assert Interpreter(io=1).run("1=1.1") == S(0)

    def test_not_equal_outside_tolerance(self) -> None:
        assert Interpreter(io=1).run("1=1.001") == S(0)

    def test_ct_zero_exact(self) -> None:
        i = Interpreter(io=1)
        i.run("⎕CT←0")
        assert i.run("1=1.001") == S(0)

    def test_ct_zero_strict(self) -> None:
        i = Interpreter(io=1)
        i.run("⎕CT←0")
        assert i.run("1=1.00000000000001") == S(0)

    def test_near_not_equal(self) -> None:
        assert Interpreter(io=1).run("1≠(1÷3)×3") == S(0)

    def test_near_less_equal(self) -> None:
        i = Interpreter(io=1)
        i.run("x←(1÷3)×3")
        assert i.run("1≤x") == S(1)

    def test_near_greater_equal(self) -> None:
        i = Interpreter(io=1)
        i.run("x←(1÷3)×3")
        assert i.run("x≥1") == S(1)

    def test_ct_affects_less_equal(self) -> None:
        assert Interpreter(io=1).run("1≤1.0000000000000001") == S(1)


class TestIndexOfTolerant:
    def test_index_of_uses_ct(self) -> None:
        assert Interpreter(io=1).run("1 2 3⍳2.0000000000000001") == S(2)

    def test_iota_tolerant(self) -> None:
        i = Interpreter(io=1)
        i.run("x←÷⍳3")
        assert i.run("x⍳0.5") == S(2)

    def test_iota_tolerant_third(self) -> None:
        i = Interpreter(io=1)
        i.run("x←÷⍳3")
        assert i.run("x⍳÷3") == S(3)


class TestMembership:
    def test_membership_found(self) -> None:
        assert Interpreter(io=1).run("3∈1 2 3 4 5") == S(1)

    def test_membership_not_found(self) -> None:
        assert Interpreter(io=1).run("6∈1 2 3 4 5") == S(0)

    def test_membership_vector(self) -> None:
        assert Interpreter(io=1).run("1 3 5∈2 3 4") == APLArray.array([3], [0, 1, 0])

    def test_membership_tolerant(self) -> None:
        i = Interpreter(io=1)
        i.run("x←(1÷3)×3")
        assert i.run("x∈1 2 3") == S(1)

    def test_membership_uses_ct(self) -> None:
        result = Interpreter(io=1).run("2.0000000000000001∈1 2 3")
        assert result == S(1)


class TestMatchExact:
    def test_match_exact(self) -> None:
        assert Interpreter(io=1).run("1≡1") == S(1)
        assert Interpreter(io=1).run("1≡2") == S(0)
