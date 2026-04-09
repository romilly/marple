"""Decode (⊥, dyadic) tests — edge cases and ISO/Dyalog spec compliance.

These tests cover dyadic ⊥ (Base Value): given a radix system in α and
a digit sequence in ω, evaluate ω as a polynomial with bases from α.

The 20 tests below were originally written on 2026-04-08 during the
post-char-migration edge-case sweep. They surfaced two ISO/Dyalog spec
violations and one straightforward crash, but the work of fixing them
uncovered the deeper scalar storage convention rot. The tests were
parked outside the test tree while the scalar migration ran (commits
46c269f → fe7499a, v0.7.26 → v0.7.40, completed 2026-04-09).

With the scalar convention fixed, the parked tests are resurrected
here as the spec-correct target for a numpy-native decode rewrite.
"""

import pytest

from marple.engine import Interpreter
from marple.errors import DomainError, LengthError
from marple.numpy_array import APLArray, S


class TestDecodeEdgeCases:
    """Edge-case sweep for dyadic ⊥ (decode)."""

    def test_decode_scalar_omega(self) -> None:
        # Single-digit number in base 10 is just the digit.
        result = Interpreter(io=1).run("10⊥7")
        assert result == S(7)

    def test_decode_scalar_omega_extends_to_alpha(self) -> None:
        # Dyalog: scalar omega extends to length of alpha.
        # 2 2 2⊥7 = 7·4 + 7·2 + 7 = 49
        result = Interpreter(io=1).run("2 2 2⊥7")
        assert result == S(49)

    def test_decode_vector_alpha_matrix_omega(self) -> None:
        # Each column of omega is a 3-digit base-2 number.
        # col0=[1,0,1]=5  col1=[1,1,0]=6
        result = Interpreter(io=1).run("2 2 2⊥3 2⍴1 1 0 1 1 0")
        assert result == APLArray.array([2], [5, 6])

    def test_decode_scalar_alpha_matrix_omega(self) -> None:
        # Scalar base 2; each column of omega is a 3-digit number.
        # col0=[1,0,1]=5  col1=[0,1,1]=3
        result = Interpreter(io=1).run("2⊥3 2⍴1 0 0 1 1 1")
        assert result == APLArray.array([2], [5, 3])

    def test_decode_mixed_base_matrix_omega(self) -> None:
        # Time conversion: each column is h/m/s.
        # col0=[1,2,3] in base 24/60/60 = 3723
        # col1=[0,0,1] in base 24/60/60 = 1
        result = Interpreter(io=1).run("24 60 60⊥3 2⍴1 0 2 0 3 1")
        assert result == APLArray.array([2], [3723, 1])

    def test_decode_empty_right(self) -> None:
        # Empty digits → 0 (the polynomial is empty).
        result = Interpreter(io=1).run("2⊥⍳0")
        assert result == S(0)

    def test_decode_length_mismatch(self) -> None:
        with pytest.raises(LengthError):
            Interpreter(io=1).run("2 2⊥1 0 1")

    def test_decode_char_omega_raises(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("2⊥'abc'")

    def test_decode_char_alpha_raises(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("'ab'⊥1 0")

    def test_decode_dtype_int(self) -> None:
        # Result of decoding integer digits should remain integer-valued.
        result = Interpreter(io=1).run("2 2 2⊥1 0 1")
        assert result == S(5)
        # Round-trip through equality is enough; check the underlying
        # data is integer, not float.
        import numpy as np
        assert np.issubdtype(result.data.dtype, np.integer)

    # ------------------------------------------------------------------
    # Spec-driven tests from the Dyalog ⊥ ("Base Value") documentation.
    # ISO standard. Any divergence is a bug.
    # ------------------------------------------------------------------

    def test_decode_spec_60_60(self) -> None:
        # 60 60⊥3 13 → 193  (3·60 + 13)
        assert Interpreter(io=1).run("60 60⊥3 13") == S(193)

    def test_decode_spec_first_element_no_effect(self) -> None:
        # Spec: "The first element of X has no effect on the result."
        # 0 60⊥3 13 must equal 60 60⊥3 13.
        assert Interpreter(io=1).run("0 60⊥3 13") == S(193)

    def test_decode_spec_scalar_alpha_extends(self) -> None:
        # Spec example: 60⊥3 13 = 193 (scalar α extends to length 2).
        assert Interpreter(io=1).run("60⊥3 13") == S(193)

    def test_decode_spec_binary(self) -> None:
        # Spec example: 2⊥1 0 1 0 = 10
        assert Interpreter(io=1).run("2⊥1 0 1 0") == S(10)

    def test_decode_spec_polynomial_base_2(self) -> None:
        # Spec polynomial-evaluation example: 2⊥1 2 3 4 = 26
        # = 1·8 + 2·4 + 3·2 + 4 = 26
        assert Interpreter(io=1).run("2⊥1 2 3 4") == S(26)

    def test_decode_spec_polynomial_base_3(self) -> None:
        # Spec polynomial-evaluation example: 3⊥1 2 3 4 = 58
        # = 1·27 + 2·9 + 3·3 + 4 = 58
        assert Interpreter(io=1).run("3⊥1 2 3 4") == S(58)

    def test_decode_spec_matrix_alpha(self) -> None:
        # Spec example: A⊥M where each row of A is a radix system.
        #   M = 3 8 ⍴ 0 0 0 0 1 1 1 1 / 0 0 1 1 0 0 1 1 / 0 1 0 1 0 1 0 1
        #   A = 4 3 ⍴ 1 1 1 / 2 2 2 / 3 3 3 / 4 4 4
        # Expected (4,8) result from the page.
        i = Interpreter(io=1)
        i.run("M←3 8⍴0 0 0 0 1 1 1 1 0 0 1 1 0 0 1 1 0 1 0 1 0 1 0 1")
        i.run("A←4 3⍴1 1 1 2 2 2 3 3 3 4 4 4")
        result = i.run("A⊥M")
        assert result == APLArray.array(
            [4, 8],
            [[0, 1, 1, 2, 1, 2, 2, 3],
             [0, 1, 2, 3, 4, 5, 6, 7],
             [0, 1, 3, 4, 9, 10, 12, 13],
             [0, 1, 4, 5, 16, 17, 20, 21]],
        )

    def test_decode_spec_scalar_alpha_matrix_omega(self) -> None:
        # Spec example: 2⊥M where M is the (3,8) matrix above.
        # Result is the column-wise base-2 decoding: 0 1 2 3 4 5 6 7.
        i = Interpreter(io=1)
        i.run("M←3 8⍴0 0 0 0 1 1 1 1 0 0 1 1 0 0 1 1 0 1 0 1 0 1 0 1")
        result = i.run("2⊥M")
        assert result == APLArray.array([8], [0, 1, 2, 3, 4, 5, 6, 7])

    def test_decode_spec_unit_axis_extension(self) -> None:
        # Spec example: extension along a unit (last) axis of α.
        #   A = 2 1 ⍴ 2 10  → shape (2,1), last axis length 1.
        # First row decodes M as base 2, second row as base 10.
        i = Interpreter(io=1)
        i.run("M←3 8⍴0 0 0 0 1 1 1 1 0 0 1 1 0 0 1 1 0 1 0 1 0 1 0 1")
        i.run("A←2 1⍴2 10")
        result = i.run("A⊥M")
        assert result == APLArray.array(
            [2, 8],
            [[0, 1, 2, 3, 4, 5, 6, 7],
             [0, 1, 10, 11, 100, 101, 110, 111]],
        )

    def test_decode_spec_float_omega(self) -> None:
        # Float digits must NOT be truncated. Per Dyalog/ISO:
        # 2⊥1.5 0.5 = 1.5·2 + 0.5 = 3.5
        result = Interpreter(io=1).run("2⊥1.5 0.5")
        assert result == S(3.5)
