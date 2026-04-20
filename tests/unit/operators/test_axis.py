"""Reduce and scan with explicit axis specifier — new engine.

Syntax: f/[k] Y, f⌿[k] Y, f\\[k] Y, f⍀[k] Y
k is a scalar integer, ⎕IO-dependent.
"""

import pytest

from marple.ports.array import APLArray, S
from marple.engine import Interpreter
from marple.errors import DomainError


class TestReduceAxis:
    def test_reduce_first_axis_rank2(self) -> None:
        result = Interpreter(io=1).run("+/[1] 2 3⍴⍳6")
        assert result == APLArray.array([3], [5, 7, 9])

    def test_reduce_last_axis_rank2(self) -> None:
        result = Interpreter(io=1).run("+/[2] 2 3⍴⍳6")
        assert result == APLArray.array([2], [6, 15])

    def test_reduce_first_glyph_with_explicit_axis(self) -> None:
        """+⌿[2] overrides ⌿'s first-axis default with explicit axis 2."""
        result = Interpreter(io=1).run("+⌿[2] 2 3⍴⍳6")
        assert result == APLArray.array([2], [6, 15])

    def test_reduce_rank3_axis1(self) -> None:
        result = Interpreter(io=1).run("+/[1] 2 3 4⍴⍳24")
        assert result.shape == [3, 4]

    def test_reduce_rank3_axis2(self) -> None:
        result = Interpreter(io=1).run("+/[2] 2 3 4⍴⍳24")
        assert result == APLArray.array([2, 4], [[15, 18, 21, 24], [51, 54, 57, 60]])

    def test_reduce_rank3_axis3(self) -> None:
        result = Interpreter(io=1).run("+/[3] 2 3 4⍴⍳24")
        assert result == APLArray.array([2, 3], [[10, 26, 42], [58, 74, 90]])


class TestScanAxis:
    def test_scan_first_axis_rank2(self) -> None:
        result = Interpreter(io=1).run("+\\[1] 2 3⍴⍳6")
        assert result == APLArray.array([2, 3], [[1, 2, 3], [5, 7, 9]])

    def test_scan_last_axis_rank2(self) -> None:
        result = Interpreter(io=1).run("+\\[2] 2 3⍴⍳6")
        assert result == APLArray.array([2, 3], [[1, 3, 6], [4, 9, 15]])

    def test_scan_first_glyph_with_explicit_axis(self) -> None:
        result = Interpreter(io=1).run("+⍀[2] 2 3⍴⍳6")
        assert result == APLArray.array([2, 3], [[1, 3, 6], [4, 9, 15]])


class TestAxisWithIo0:
    def test_reduce_axis0_under_io0(self) -> None:
        """Under ⎕IO=0, axis 0 is the first axis (size-2)."""
        result = Interpreter(io=0).run("+/[0] 2 3⍴⍳6")
        # With ⎕IO=0, ⍳6 = 0..5, 2 3⍴ gives [[0,1,2],[3,4,5]].
        # Reduce first axis: 0+3, 1+4, 2+5 = 3 5 7
        assert result == APLArray.array([3], [3, 5, 7])


class TestAxisErrors:
    def test_axis_out_of_range(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("+/[4] 2 3 4⍴⍳24")

    def test_axis_must_be_scalar(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("+/[1 2] 2 3⍴⍳6")


class TestReduceScanRightToLeft:
    """APL reduce/scan is right-to-left along the axis, including first-axis
    forms (⌿, ⍀). Exposed by non-associative operators like -.
    """

    def test_minus_reduce_first_axis(self) -> None:
        """-⌿ 3 2⍴⍳6: [[1,2],[3,4],[5,6]] → 1-(3-5), 2-(4-6) → 3, 4."""
        result = Interpreter(io=1).run("-⌿ 3 2⍴⍳6")
        assert result == APLArray.array([2], [3, 4])

    def test_minus_scan_first_axis(self) -> None:
        """-⍀ 3 2⍴⍳6: per-column right-to-left prefix scans."""
        result = Interpreter(io=1).run("-⍀ 3 2⍴⍳6")
        assert result == APLArray.array([3, 2], [[1, 2], [-2, -2], [3, 4]])
