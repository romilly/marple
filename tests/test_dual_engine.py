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


class TestProducts:
    def test_inner_product(self, engine: object) -> None:
        assert engine.run("1 2 3+.×4 5 6") == S(32)

    def test_outer_product(self, engine: object) -> None:
        result = engine.run("1 2 3∘.×4 5")
        assert result == APLArray([3, 2], [4, 5, 8, 10, 12, 15])

    def test_outer_product_addition(self, engine: object) -> None:
        result = engine.run("1 2 3∘.+10 20")
        assert result == APLArray([3, 2], [11, 21, 12, 22, 13, 23])

    def test_matrix_multiply(self, engine: object) -> None:
        result = engine.run("(2 2⍴1 2 3 4)+.×(2 2⍴5 6 7 8)")
        assert result == APLArray([2, 2], [19, 22, 43, 50])

    def test_matrix_multiply_non_square(self, engine: object) -> None:
        engine.run("A←2 3⍴⍳6")
        engine.run("B←3 2⍴⍳6")
        result = engine.run("A+.×B")
        assert result.shape == [2, 2]
        assert list(result.data) == [22, 28, 49, 64]

    def test_matrix_vector_inner(self, engine: object) -> None:
        engine.run("M←2 3⍴⍳6")
        result = engine.run("M+.×1 2 3")
        assert result.shape == [2]
        assert list(result.data) == [14, 32]

    def test_vector_matrix_inner(self, engine: object) -> None:
        engine.run("M←2 3⍴⍳6")
        result = engine.run("1 2+.×M")
        assert result.shape == [3]
        assert list(result.data) == [9, 12, 15]

    def test_outer_equality(self, engine: object) -> None:
        result = engine.run("1 2 3∘.=1 3")
        assert result == APLArray([3, 2], [1, 0, 0, 0, 0, 1])

    def test_outer_multiplication_table(self, engine: object) -> None:
        result = engine.run("(⍳3)∘.×⍳4")
        assert result == APLArray([3, 4], [
            1, 2, 3, 4,
            2, 4, 6, 8,
            3, 6, 9, 12,
        ])


class TestSystemFunctionsExtra:
    def test_ucs_to_char(self, engine: object) -> None:
        result = engine.run("⎕UCS 65")
        assert result == S("A")

    def test_ucs_to_code(self, engine: object) -> None:
        result = engine.run("⎕UCS 'A'")
        assert result == APLArray([1], [65])

    def test_dr_integer(self, engine: object) -> None:
        result = engine.run("⎕DR 42")
        assert result == S(323)

    def test_dr_char(self, engine: object) -> None:
        result = engine.run("⎕DR 'hello'")
        assert result == S(80)

    def test_signal(self, engine: object) -> None:
        import pytest
        from marple.errors import DomainError
        with pytest.raises(DomainError):
            engine.run("⎕SIGNAL 3")


class TestDyadicFormat:
    def test_dyadic_format_width(self, engine: object) -> None:
        result = engine.run("5⍕42")
        assert result.shape == [5]

    def test_dyadic_format_width_precision(self, engine: object) -> None:
        result = engine.run("8 2⍕3.14159")
        chars = "".join(str(c) for c in result.data)
        assert "3.14" in chars


class TestBracketIndex:
    def test_vector_index(self, engine: object) -> None:
        assert engine.run("(⍳5)[2]") == S(2)

    def test_vector_multiple(self, engine: object) -> None:
        engine.run("v←10 20 30 40 50")
        assert engine.run("v[1 3 5]") == APLArray([3], [10, 30, 50])

    def test_matrix_index(self, engine: object) -> None:
        assert engine.run("(3 4⍴⍳12)[2;3]") == S(7)

    def test_matrix_row(self, engine: object) -> None:
        engine.run("M←2 3⍴⍳6")
        assert engine.run("M[1;]") == APLArray([3], [1, 2, 3])

    def test_matrix_column(self, engine: object) -> None:
        result = engine.run("(2 3⍴⍳6)[;2]")
        assert result == APLArray([2], [2, 5])

    def test_scalar_index_shape(self, engine: object) -> None:
        engine.run("v←10 20 30")
        result = engine.run("v[2]")
        assert result.shape == []

    def test_matrix_index_shape(self, engine: object) -> None:
        engine.run("v←10 20 30 40 50")
        result = engine.run("v[2 3⍴1 2 3 4 5 1]")
        assert result.shape == [2, 3]

    def test_string_index(self, engine: object) -> None:
        result = engine.run("'abcde'[2 3⍴1 2 3 4 5 1]")
        assert result.shape == [2, 3]
        assert result.data == ['a', 'b', 'c', 'd', 'e', 'a']


class TestDeal:
    def test_deal(self, engine: object) -> None:
        result = engine.run("3?10")
        assert result.shape == [3]
        values = [int(v) for v in result.data]
        assert len(set(values)) == 3
        assert all(1 <= v <= 10 for v in values)
