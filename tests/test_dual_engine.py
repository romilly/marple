"""Tests that run against both old and new engines via the engine fixture."""

from marple.arraymodel import APLArray, S


class TestScalars:
    def test_single_number(self, engine: object) -> None:
        assert engine.run("5") == S(5)

    def test_negative_number(self, engine: object) -> None:
        assert engine.run("¯3") == S(-3)

    def test_float(self, engine: object) -> None:
        assert engine.run("3.14") == S(3.14)


class TestMonadic:
    def test_negate(self, engine: object) -> None:
        assert engine.run("-5") == S(-5)

    def test_reciprocal(self, engine: object) -> None:
        assert engine.run("÷4") == S(0.25)

    def test_ceiling(self, engine: object) -> None:
        assert engine.run("⌈2.3") == S(3)

    def test_floor(self, engine: object) -> None:
        assert engine.run("⌊2.7") == S(2)


class TestDyadic:
    def test_add(self, engine: object) -> None:
        assert engine.run("3+4") == S(7)

    def test_subtract(self, engine: object) -> None:
        assert engine.run("5-3") == S(2)

    def test_multiply(self, engine: object) -> None:
        assert engine.run("3×4") == S(12)

    def test_divide(self, engine: object) -> None:
        assert engine.run("10÷4") == S(2.5)

    def test_maximum(self, engine: object) -> None:
        assert engine.run("3⌈5") == S(5)

    def test_minimum(self, engine: object) -> None:
        assert engine.run("3⌊5") == S(3)


class TestRightToLeft:
    def test_long_right_scope(self, engine: object) -> None:
        assert engine.run("1+2×3") == S(7)

    def test_chained_operations(self, engine: object) -> None:
        assert engine.run("2×3+4") == S(14)


class TestParens:
    def test_parens_override(self, engine: object) -> None:
        assert engine.run("(1+2)×3") == S(9)


class TestVectors:
    def test_vector_literal(self, engine: object) -> None:
        assert engine.run("1 2 3") == APLArray([3], [1, 2, 3])

    def test_vector_addition(self, engine: object) -> None:
        assert engine.run("1 2 3+4 5 6") == APLArray([3], [5, 7, 9])

    def test_scalar_plus_vector(self, engine: object) -> None:
        assert engine.run("10+1 2 3") == APLArray([3], [11, 12, 13])

    def test_negate_vector(self, engine: object) -> None:
        assert engine.run("-1 2 3") == APLArray([3], [-1, -2, -3])


class TestAssignment:
    def test_assign_and_use(self, engine: object) -> None:
        engine.run("x←5")
        assert engine.run("x+3") == S(8)

    def test_assign_returns_value(self, engine: object) -> None:
        assert engine.run("x←5") == S(5)


class TestComments:
    def test_comment_ignored(self, engine: object) -> None:
        assert engine.run("3+4 ⍝ add them") == S(7)

    def test_comment_only(self, engine: object) -> None:
        assert engine.run("⍝ this is a comment") == S(0)


class TestComparisons:
    def test_less_than(self, engine: object) -> None:
        assert engine.run("2<3") == S(1)
        assert engine.run("3<2") == S(0)

    def test_equal(self, engine: object) -> None:
        assert engine.run("2=2") == S(1)
        assert engine.run("2=3") == S(0)

    def test_greater_than(self, engine: object) -> None:
        assert engine.run("3>2") == S(1)

    def test_not_equal(self, engine: object) -> None:
        assert engine.run("2≠3") == S(1)
        assert engine.run("2≠2") == S(0)


class TestDyadicStructural:
    def test_index_of(self, engine: object) -> None:
        assert engine.run("3 1 4 1 5⍳4") == S(3)

    def test_membership(self, engine: object) -> None:
        assert engine.run("2 3∈1 2 3 4 5") == APLArray([2], [1, 1])

    def test_from(self, engine: object) -> None:
        assert engine.run("2⌷10 20 30") == S(20)

    def test_match(self, engine: object) -> None:
        assert engine.run("(1 2 3)≡(1 2 3)") == S(1)
        assert engine.run("(1 2 3)≡(1 2 4)") == S(0)


class TestMonadicExtra:
    def test_grade_up(self, engine: object) -> None:
        assert engine.run("⍋3 1 4 1 5") == APLArray([5], [2, 4, 1, 3, 5])

    def test_grade_down(self, engine: object) -> None:
        assert engine.run("⍒3 1 4 1 5") == APLArray([5], [5, 3, 1, 2, 4])

    def test_format(self, engine: object) -> None:
        result = engine.run("⍕42")
        assert result.shape == [2]
        assert list(result.data) == ["4", "2"]

    def test_execute(self, engine: object) -> None:
        assert engine.run("⍎'2+3'") == S(5)


class TestDfns:
    def test_simple_dfn(self, engine: object) -> None:
        engine.run("double←{⍵+⍵}")
        assert engine.run("double 3") == S(6)

    def test_dyadic_dfn(self, engine: object) -> None:
        engine.run("add←{⍺+⍵}")
        assert engine.run("3 add 4") == S(7)

    def test_guard(self, engine: object) -> None:
        engine.run("abs←{⍵≥0:⍵ ⋄ -⍵}")
        assert engine.run("abs 5") == S(5)
        assert engine.run("abs ¯3") == S(3)


class TestOperators:
    def test_reduce(self, engine: object) -> None:
        assert engine.run("+/⍳5") == S(15)

    def test_scan(self, engine: object) -> None:
        assert engine.run("+\\⍳5") == APLArray([5], [1, 3, 6, 10, 15])

    def test_user_dop(self, engine: object) -> None:
        engine.run("twice←{⍺⍺ ⍺⍺ ⍵}")
        assert engine.run("(-)twice 5") == S(5)
