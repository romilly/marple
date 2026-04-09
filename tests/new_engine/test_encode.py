"""Encode (⊤, dyadic) tests — edge cases and ISO/Dyalog spec compliance.

These tests cover dyadic ⊤ (Representation): given a radix system in α
and value(s) in ω, represent ω in the number system defined by α.

Result shape per spec: (⍴α),⍴ω — the α dimensions come FIRST, then
the ω dimensions. For higher-rank α, the radix vectors are the
vectors along α's FIRST axis (so for an (n,k) matrix α, the k columns
are k independent radix systems each of length n).

Each test's docstring shows the exact APL expression so it can be
verified against Dyalog directly. Treat Dyalog/ISO as the source of
truth — if any test diverges, fix the test, not the spec.
"""

import pytest

from marple.engine import Interpreter
from marple.errors import DomainError
from marple.numpy_array import APLArray, S


class TestEncodeEdgeCases:
    """Edge-case sweep for dyadic ⊤ (encode)."""

    # ------------------------------------------------------------------
    # Scalar / vector α with scalar / vector ω
    # ------------------------------------------------------------------

    def test_encode_scalar_alpha_scalar_omega(self) -> None:
        # 2⊤7 → 1   (one binary digit; 7 wraps to residue 7|2 = 1)
        # Result shape (⍴α),⍴ω = (),() = scalar.
        assert Interpreter(io=1).run("2⊤7") == S(1)

    def test_encode_scalar_alpha_vector_omega(self) -> None:
        # 2⊤1 2 3 → 1 0 1
        # Each ω element is encoded into 1 binary digit (mod 2).
        # Result shape (),(3) = (3,).
        result = Interpreter(io=1).run("2⊤1 2 3")
        assert result == APLArray.array([3], [1, 0, 1])

    def test_encode_vector_alpha_scalar_omega(self) -> None:
        # 2 2 2⊤7 → 1 1 1
        # Result shape (3,),() = (3,).
        result = Interpreter(io=1).run("2 2 2⊤7")
        assert result == APLArray.array([3], [1, 1, 1])

    def test_encode_vector_alpha_vector_omega(self) -> None:
        # 2 2 2⊤1 2 3 → 3-digit binary representation of each value.
        # Result shape (3,),(3,) = (3,3). Each COLUMN is one encoded value.
        #   col0 = encoding of 1 = 0 0 1
        #   col1 = encoding of 2 = 0 1 0
        #   col2 = encoding of 3 = 0 1 1
        result = Interpreter(io=1).run("2 2 2⊤1 2 3")
        assert result == APLArray.array(
            [3, 3],
            [[0, 0, 0],
             [0, 1, 1],
             [1, 0, 1]],
        )

    def test_encode_mixed_radix_scalar_omega(self) -> None:
        # 24 60 60⊤3723 → 1 2 3   (1 hour, 2 minutes, 3 seconds)
        # 1·3600 + 2·60 + 3 = 3723.
        result = Interpreter(io=1).run("24 60 60⊤3723")
        assert result == APLArray.array([3], [1, 2, 3])

    # ------------------------------------------------------------------
    # 0-radix: full representation (no further wrapping)
    # ------------------------------------------------------------------

    def test_encode_leading_zero_radix_preserves_value(self) -> None:
        # 0 10⊤125 → 12 5
        # The trailing radix 10 takes one decimal digit; the 0 captures
        # the remaining carry without further mod.
        result = Interpreter(io=1).run("0 10⊤125")
        assert result == APLArray.array([2], [12, 5])

    def test_encode_leading_zero_radix_small_value(self) -> None:
        # 0 10⊤5 → 0 5   (the carry is 0 after extracting the units digit)
        result = Interpreter(io=1).run("0 10⊤5")
        assert result == APLArray.array([2], [0, 5])

    # ------------------------------------------------------------------
    # Wrap-around (residue) when ω exceeds the system's range
    # ------------------------------------------------------------------

    def test_encode_overflow_wraps_to_residue(self) -> None:
        # 2⊤7 → 1   (already covered; the 1-digit binary system holds 0..1,
        # so 7 wraps to 7|2 = 1)
        assert Interpreter(io=1).run("2⊤7") == S(1)

    def test_encode_overflow_2_2_omega_exceeds(self) -> None:
        # 2 2⊤5 → 0 1   (2 binary digits hold 0..3, so 5 wraps to 5|4 = 1)
        # Encoding 1 in binary with 2 digits = 0 1.
        result = Interpreter(io=1).run("2 2⊤5")
        assert result == APLArray.array([2], [0, 1])

    # ------------------------------------------------------------------
    # Float ω: must be preserved per the spec example
    # ------------------------------------------------------------------

    def test_encode_float_spec_example(self) -> None:
        # 0 1⊤1.25 10.5 →
        #   1    10
        #   0.25 0.5
        # The trailing radix 1 extracts the fractional part; the 0
        # captures the integer part.
        result = Interpreter(io=1).run("0 1⊤1.25 10.5")
        assert result == APLArray.array(
            [2, 2],
            [[1.0, 10.0],
             [0.25, 0.5]],
        )

    def test_encode_float_dtype_preserved(self) -> None:
        # 2⊤1.5 → 1.5  (1-digit "binary" of 1.5; 1.5 mod 2 = 1.5)
        result = Interpreter(io=1).run("2⊤1.5")
        assert result == S(1.5)

    # ------------------------------------------------------------------
    # Domain rejection — encode requires SIMPLE NUMERIC arrays
    # ------------------------------------------------------------------

    def test_encode_char_omega_raises(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("2⊤'a'")

    def test_encode_char_alpha_raises(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("'ab'⊤1")

    # ------------------------------------------------------------------
    # Higher-rank α — vectors along the FIRST axis are radix systems
    # ------------------------------------------------------------------

    def test_encode_spec_matrix_alpha(self) -> None:
        # The spec example with three different number systems applied
        # to the decimal value 75:
        #   A is an (8,3) matrix where each COLUMN is a radix system
        #     col 0: 2 2 2 2 2 2 2 2     (binary in 8 digits)
        #     col 1: 0 0 0 0 0 8 8 8     (octal, last 3 digits, 0 carries)
        #     col 2: 0 0 0 0 0 0 16 16   (hex, last 3 digits, 0 carries)
        # Wait — actually re-checking the spec: A col 1 is 0 0 0 0 0 8 8 8
        # which only has 3 trailing 8s. 75 in octal is 113 (3 digits). ✓
        # A col 2 is 0 0 0 0 0 0 16 16 — 75 in hex is 4B (2 digits). ✓
        i = Interpreter(io=1)
        i.run("A←8 3⍴2 0 0 2 0 0 2 0 0 2 0 0 2 8 0 2 8 0 2 8 16 2 8 16")
        result = i.run("A⊤75")
        assert result == APLArray.array(
            [8, 3],
            [[0, 0,  0],
             [1, 0,  0],
             [0, 0,  0],
             [0, 0,  0],
             [1, 0,  0],
             [0, 1,  0],
             [1, 1,  4],
             [1, 3, 11]],
        )

    # ------------------------------------------------------------------
    # Spec example: vector α with vector ω
    # ------------------------------------------------------------------

    def test_encode_spec_10_to_5_15_125(self) -> None:
        # 10⊤5 15 125 → 5 5 5
        # Each value mod 10 (1-digit base 10).
        result = Interpreter(io=1).run("10⊤5 15 125")
        assert result == APLArray.array([3], [5, 5, 5])

    def test_encode_spec_0_10_to_5_15_125(self) -> None:
        # 0 10⊤5 15 125 →
        #    0  1 12
        #    5  5  5
        # Each column is the 2-element encoding of one value.
        result = Interpreter(io=1).run("0 10⊤5 15 125")
        assert result == APLArray.array(
            [2, 3],
            [[0, 1, 12],
             [5, 5,  5]],
        )

    # ------------------------------------------------------------------
    # Round-trip with decode (the inverse identity)
    # ------------------------------------------------------------------

    def test_encode_decode_round_trip_scalar(self) -> None:
        # 2 2 2⊥2 2 2⊤7 → 7
        result = Interpreter(io=1).run("2 2 2⊥2 2 2⊤7")
        assert result == S(7)

    def test_encode_decode_round_trip_mixed(self) -> None:
        # 24 60 60⊥24 60 60⊤3723 → 3723
        result = Interpreter(io=1).run("24 60 60⊥24 60 60⊤3723")
        assert result == S(3723)
