"""Core interpreter tests."""

from marple.engine import Interpreter
from marple.adapters.numpy_array_builder import BUILDER
S = BUILDER.S


class TestComments:
    def test_comment_only(self) -> None:
        assert Interpreter(io=1).run("⍝ this is a comment") == S(0)

    def test_comment_with_box_drawing(self) -> None:
        assert Interpreter(io=1).run("⍝ ═══════════════════") == S(0)

    def test_comment_only_no_space(self) -> None:
        assert Interpreter(io=1).run("⍝comment") == S(0)

    def test_comment_ignored(self) -> None:
        assert Interpreter(io=1).run("3+4 ⍝ add them") == S(7)


class TestScalars:
    def test_single_number(self) -> None:
        assert Interpreter(io=1).run("5") == S(5)

    def test_negative_number(self) -> None:
        assert Interpreter(io=1).run("¯3") == S(-3)

    def test_float(self) -> None:
        assert Interpreter(io=1).run("3.14") == S(3.14)


class TestMonadic:
    def test_negate(self) -> None:
        assert Interpreter(io=1).run("-5") == S(-5)

    def test_reciprocal(self) -> None:
        assert Interpreter(io=1).run("÷4") == S(0.25)

    def test_ceiling(self) -> None:
        assert Interpreter(io=1).run("⌈2.3") == S(3)

    def test_floor(self) -> None:
        assert Interpreter(io=1).run("⌊2.7") == S(2)


class TestDyadic:
    def test_add(self) -> None:
        assert Interpreter(io=1).run("3+4") == S(7)

    def test_subtract(self) -> None:
        assert Interpreter(io=1).run("5-3") == S(2)

    def test_multiply(self) -> None:
        assert Interpreter(io=1).run("3×4") == S(12)

    def test_divide(self) -> None:
        assert Interpreter(io=1).run("10÷4") == S(2.5)

    def test_maximum(self) -> None:
        assert Interpreter(io=1).run("3⌈5") == S(5)

    def test_minimum(self) -> None:
        assert Interpreter(io=1).run("3⌊5") == S(3)


class TestRightToLeft:
    def test_long_right_scope(self) -> None:
        assert Interpreter(io=1).run("1+2×3") == S(7)

    def test_chained_operations(self) -> None:
        assert Interpreter(io=1).run("2×3+4") == S(14)


class TestParens:
    def test_parens_override(self) -> None:
        assert Interpreter(io=1).run("(1+2)×3") == S(9)


class TestVectors:
    def test_vector_literal(self) -> None:
        assert Interpreter(io=1).run("1 2 3") == BUILDER.apl_array([3], [1, 2, 3])

    def test_vector_addition(self) -> None:
        assert Interpreter(io=1).run("1 2 3+4 5 6") == BUILDER.apl_array([3], [5, 7, 9])

    def test_scalar_plus_vector(self) -> None:
        assert Interpreter(io=1).run("10+1 2 3") == BUILDER.apl_array([3], [11, 12, 13])

    def test_negate_vector(self) -> None:
        assert Interpreter(io=1).run("-1 2 3") == BUILDER.apl_array([3], [-1, -2, -3])


class TestAssignment:
    def test_assign_and_use(self) -> None:
        i = Interpreter(io=1)
        i.run("x←5")
        assert i.run("x+3") == S(8)

    def test_assign_returns_value(self) -> None:
        assert Interpreter(io=1).run("x←5") == S(5)

    def test_chained_assign(self) -> None:
        i = Interpreter(io=1)
        i.run("y←1+x←⍳4")
        assert i.run("x") == BUILDER.apl_array([4], [1, 2, 3, 4])
        assert i.run("y") == BUILDER.apl_array([4], [2, 3, 4, 5])


class TestStatementSeparator:
    def test_two_statements_returns_last(self) -> None:
        assert Interpreter(io=1).run("3⋄5") == S(5)

    def test_assignment_then_use(self) -> None:
        assert Interpreter(io=1).run("x←3⋄x+1") == S(4)

    def test_multiple_assignments(self) -> None:
        assert Interpreter(io=1).run("x←2⋄y←3⋄x+y") == S(5)
