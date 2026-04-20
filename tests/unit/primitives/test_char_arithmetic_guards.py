"""Domain guards: arithmetic on character arrays must raise DomainError.

Step 1 of the character uint32 migration plan
(plan/plan-char-uint32-migration.md). Comparison and equality operators
are NOT guarded — they are legitimately defined for character data with
comparison tolerance forced to zero.

The guards must catch character arrays in *either* representation
(list[str] now, uint32 ndarray later), so they need to live before the
is_numeric_array fast path which will become true for uint32 chars.
"""

import pytest

from marple.engine import Interpreter
from marple.errors import DomainError


class TestAddGuard:
    def test_add_char_char(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("'a'+'b'")

    def test_add_char_num(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("'a'+1")

    def test_add_num_char(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("1+'a'")

    def test_add_char_vector(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("'abc'+1 2 3")


class TestSubtractGuard:
    def test_subtract_char_char(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("'b'-'a'")

    def test_subtract_num_char(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("1-'a'")


class TestMultiplyGuard:
    def test_multiply_num_char(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("2×'a'")

    def test_multiply_char_char(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("'a'×'b'")


class TestDivideGuard:
    def test_divide_char_num(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("'a'÷2")

    def test_divide_num_char(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("2÷'a'")


class TestPowerGuard:
    def test_power_char_num(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("'a'*2")

    def test_power_num_char(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("2*'a'")


class TestResidueGuard:
    def test_residue_num_char(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("2|'a'")

    def test_residue_char_num(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("'a'|2")


class TestMaximumGuard:
    def test_maximum_num_char(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("2⌈'a'")

    def test_maximum_char_char(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("'a'⌈'b'")


class TestMinimumGuard:
    def test_minimum_num_char(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("2⌊'a'")

    def test_minimum_char_char(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("'a'⌊'b'")


class TestLogarithmGuard:
    def test_logarithm_num_char(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("2⍟'a'")

    def test_logarithm_char_num(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("'a'⍟2")


class TestCircularGuard:
    def test_circular_num_char(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("1○'a'")

    def test_circular_char_num(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("'a'○1")


class TestBinomialGuard:
    def test_binomial_num_char(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("2!'a'")

    def test_binomial_char_num(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("'a'!2")


class TestMonadicArithmeticGuards:
    def test_conjugate_char(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("+'a'")

    def test_negate_char(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("-'a'")

    def test_signum_char(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("×'a'")

    def test_reciprocal_char(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("÷'a'")

    def test_ceiling_char(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("⌈'a'")

    def test_floor_char(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("⌊'a'")

    def test_exponential_char(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("*'a'")

    def test_natural_log_char(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("⍟'a'")

    def test_absolute_value_char(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("|'a'")

    def test_pi_times_char(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("○'a'")

    def test_factorial_char(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("!'a'")

    def test_negate_char_vector(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("-'abc'")


class TestReduceScanCharGuards:
    """Reduce and scan with arithmetic operators on character data must
    raise DomainError, not silently sum codepoints."""

    def test_reduce_add_chars(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("+/'abc'")

    def test_reduce_subtract_chars(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("-/'abc'")

    def test_reduce_multiply_chars(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("×/'abc'")

    def test_reduce_divide_chars(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("÷/'abc'")

    def test_reduce_power_chars(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("*/'abc'")

    def test_reduce_residue_chars(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("|/'abc'")

    def test_reduce_logical_and_chars(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("∧/'abc'")

    def test_scan_add_chars(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("+\\'abc'")

    def test_scan_multiply_chars(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("×\\'abc'")


class TestReduceScanOnCharsStillWorks:
    """Min, max, and equality reductions on chars are well-defined
    (they compare codepoints) and must still work."""

    def test_reduce_max_chars(self) -> None:
        # ⌈/'abc' should return the maximum codepoint as a char ('c')
        # — but for now we accept it returning a numeric scalar (99)
        # because the result-as-char fix is a separate concern.
        result = Interpreter(io=1).run("⌈/'abc'")
        # Either char 'c' or numeric 99 — just don't raise.
        assert result.is_scalar()

    def test_reduce_min_chars(self) -> None:
        result = Interpreter(io=1).run("⌊/'abc'")
        assert result.is_scalar()


class TestComparisonStillWorks:
    """Sanity: Step 1 must NOT touch comparison operators."""

    def test_equal_char_char(self) -> None:
        from marple.ports.array import S
        assert Interpreter(io=1).run("'a'='a'") == S(1)

    def test_less_than_char_char(self) -> None:
        from marple.ports.array import S
        assert Interpreter(io=1).run("'a'<'b'") == S(1)

    def test_match_char_char(self) -> None:
        from marple.ports.array import S
        assert Interpreter(io=1).run("'abc'≡'abc'") == S(1)
