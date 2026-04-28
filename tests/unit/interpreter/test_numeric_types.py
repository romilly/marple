"""Numeric type tests — new engine.

Tests that arithmetic correctly handles int/float/boolean dtypes,
overflow, and cross-dtype operations.
"""

import pytest

from marple.ports.array import APLArray, S, maybe_upcast
from marple.backend_functions import maybe_downcast
import numpy as np
from marple.engine import Interpreter


class TestArithmeticUpcastDowncast:
    def test_add_integers_gives_integer(self) -> None:
        result = Interpreter(io=1).run("2+3")
        assert result == S(5)
        assert np.issubdtype(result.data.dtype, np.integer)

    def test_add_large_no_overflow(self) -> None:
        assert Interpreter(io=1).run("20000+20000") == S(40000)

    def test_multiply_large_no_overflow(self) -> None:
        assert Interpreter(io=1).run("200×200") == S(40000)

    def test_division_stays_float(self) -> None:
        result = Interpreter(io=1).run("1÷3")
        assert np.issubdtype(result.data.dtype, np.floating)

    def test_add_floats_downcast_to_integer(self) -> None:
        result = Interpreter(io=1).run("1.5+1.5")
        assert result == S(3)
        assert np.issubdtype(result.data.dtype, np.integer)


class TestReduceScanOverflow:
    def test_reduce_add_overflows_int32(self) -> None:
        assert Interpreter(io=1).run("+/2000000000 2000000000") == S(4000000000)

    def test_reduce_multiply_overflows_int32(self) -> None:
        assert Interpreter(io=1).run("×/100000 100000") == S(10000000000)

    def test_reduce_add_small_stays_integer(self) -> None:
        result = Interpreter(io=1).run("+/1 2 3")
        assert result == S(6)
        assert np.issubdtype(result.data.dtype, np.integer)

    def test_scan_add_overflows_int32(self) -> None:
        result = Interpreter(io=1).run("+\\2000000000 2000000000")
        assert list(result.data) == [2000000000, 4000000000]


class TestProductOverflow:
    def test_outer_product_overflows_int32(self) -> None:
        result = Interpreter(io=1).run("100000 200000∘.×100000 200000")
        assert result == APLArray.array([2, 2],
            [[10000000000, 20000000000], [20000000000, 40000000000]])

    def test_outer_product_small_is_integer(self) -> None:
        result = Interpreter(io=1).run("1 2∘.+3 4")
        assert result == APLArray.array([2, 2], [[4, 5], [5, 6]])
        val = result.data.flat[0]
        assert int(val) == val  # is a whole number


class TestBooleanDtype:
    def test_comparison_produces_uint8(self) -> None:
        result = Interpreter(io=1).run("1 2 3=1 3 3")
        assert str(result.data.dtype) == "uint8"

    def test_less_than_produces_uint8(self) -> None:
        result = Interpreter(io=1).run("1 2 3<2 2 2")
        assert str(result.data.dtype) == "uint8"

    def test_not_produces_uint8(self) -> None:
        result = Interpreter(io=1).run("~1 0 1")
        assert str(result.data.dtype) == "uint8"

    def test_lcm_integer_values(self) -> None:
        result = Interpreter(io=1).run("1 0 1∧1 1 0")
        assert result == APLArray.array([3], [1, 0, 0])

    def test_gcd_integer_values(self) -> None:
        result = Interpreter(io=1).run("1 0 1∨0 1 0")
        assert result == APLArray.array([3], [1, 1, 1])

    def test_boolean_values_correct(self) -> None:
        result = Interpreter(io=1).run("1 2 3=1 3 3")
        assert list(result.data) == [1, 0, 1]

    def test_boolean_in_arithmetic(self) -> None:
        result = Interpreter(io=1).run("2+(1 2 3=1 3 3)")
        assert list(result.data) == [3, 2, 3]

    def test_replicate_with_boolean(self) -> None:
        result = Interpreter(io=1).run("(3>⍳5)/⍳5")
        assert list(result.data) == [1, 2]


class TestCrossDtypeArithmetic:
    def test_int_add_int(self) -> None:
        result = Interpreter(io=1).run("1 2 3+4 5 6")
        assert list(result.data) == [5, 7, 9]
        assert isinstance(result.data.tolist()[0], int)

    def test_int_multiply_int(self) -> None:
        assert list(Interpreter(io=1).run("2 3×4 5").data) == [8, 15]

    def test_int_subtract_int(self) -> None:
        assert list(Interpreter(io=1).run("10 20-3 7").data) == [7, 13]

    def test_float_add_float(self) -> None:
        assert list(Interpreter(io=1).run("1.5 2.5+3.5 4.5").data) == [5, 7]

    def test_float_multiply_float(self) -> None:
        i = Interpreter(io=1)
        i.run("v←1.5 2.0")
        assert list(i.run("v×0.5 3.0").data) == [0.75, 6]

    def test_int_add_float(self) -> None:
        assert list(Interpreter(io=1).run("1 2 3+0.5 0.5 0.5").data) == [1.5, 2.5, 3.5]

    def test_float_add_int(self) -> None:
        assert list(Interpreter(io=1).run("0.5 1.5+1 2").data) == [1.5, 3.5]

    def test_int_multiply_float(self) -> None:
        assert list(Interpreter(io=1).run("2 3×1.5 2.5").data) == [3, 7.5]

    def test_bool_add_int(self) -> None:
        i = Interpreter(io=1)
        i.run("b←1 2 3=1 3 3")
        assert list(i.run("b+10 20 30").data) == [11, 20, 31]

    def test_int_add_bool(self) -> None:
        i = Interpreter(io=1)
        i.run("b←1 2 3=1 3 3")
        assert list(i.run("10 20 30+b").data) == [11, 20, 31]

    def test_int_multiply_bool(self) -> None:
        i = Interpreter(io=1)
        i.run("b←1 2 3=1 3 3")
        assert list(i.run("10 20 30×b").data) == [10, 0, 30]

    def test_bool_add_float(self) -> None:
        i = Interpreter(io=1)
        i.run("b←1 2 3=1 3 3")
        assert list(i.run("b+0.5 1.5 2.5").data) == [1.5, 1.5, 3.5]

    def test_float_multiply_bool(self) -> None:
        i = Interpreter(io=1)
        i.run("b←1 2 3=1 3 3")
        result = i.run("3.14 2.71 1.41×b")
        assert result.data.tolist()[1] == 0

    def test_bool_add_bool(self) -> None:
        i = Interpreter(io=1)
        i.run("a←1 0 1=1 1 1")
        i.run("b←1 1 0=1 1 1")
        assert list(i.run("a+b").data) == [2, 1, 1]

    def test_bool_multiply_bool(self) -> None:
        i = Interpreter(io=1)
        i.run("a←1 0 1=1 1 1")
        i.run("b←1 1 0=1 1 1")
        assert list(i.run("a×b").data) == [1, 0, 0]

    def test_scalar_int_add_float_vector(self) -> None:
        assert list(Interpreter(io=1).run("10+0.5 1.5 2.5").data) == [10.5, 11.5, 12.5]

    def test_scalar_float_multiply_int_vector(self) -> None:
        assert list(Interpreter(io=1).run("0.5×2 4 6").data) == [1, 2, 3]

    def test_scalar_int_add_bool_vector(self) -> None:
        i = Interpreter(io=1)
        i.run("b←1 2 3=1 3 3")
        assert list(i.run("100+b").data) == [101, 100, 101]


class TestCrossDtypeReduce:
    def test_reduce_int(self) -> None:
        assert Interpreter(io=1).run("+/1 2 3 4") == S(10)

    def test_reduce_float(self) -> None:
        result = Interpreter(io=1).run("+/0.1 0.2 0.3")
        assert abs(result.data.item() - 0.6) < 1e-10

    def test_reduce_bool(self) -> None:
        i = Interpreter(io=1)
        i.run("b←1 2 3 4 5>3")
        assert i.run("+/b") == S(2)

    def test_reduce_multiply_bool(self) -> None:
        i = Interpreter(io=1)
        i.run("b←1 1 1=1 1 1")
        assert i.run("×/b") == S(1)


class TestCrossDtypeProducts:
    def test_inner_product_int(self) -> None:
        assert Interpreter(io=1).run("1 2 3+.×4 5 6") == S(32)

    def test_inner_product_float(self) -> None:
        assert Interpreter(io=1).run("1.0 2.0+.×3.0 4.0") == S(11)

    def test_inner_product_mixed(self) -> None:
        assert Interpreter(io=1).run("1 2+.×0.5 1.5") == S(3.5)

    def test_inner_product_bool(self) -> None:
        i = Interpreter(io=1)
        i.run("a←1 0 1=1 1 1")
        i.run("b←1 1 0=1 1 1")
        assert i.run("a+.×b") == S(1)

    def test_outer_product_int(self) -> None:
        assert Interpreter(io=1).run("1 2∘.×3 4") == APLArray.array([2, 2], [[3, 4], [6, 8]])

    def test_outer_product_float(self) -> None:
        result = Interpreter(io=1).run("0.5 1.5∘.+0.1 0.2")
        assert abs(result.data.flat[0] - 0.6) < 1e-10

    def test_outer_product_mixed(self) -> None:
        assert Interpreter(io=1).run("1 2∘.×0.5 1.5") == APLArray.array([2, 2], [[0.5, 1.5], [1.0, 3.0]])

    def test_outer_product_bool(self) -> None:
        i = Interpreter(io=1)
        i.run("a←1 0=1 1")
        i.run("b←0 1=1 1")
        assert i.run("a∘.∧b") == APLArray.array([2, 2], [[0, 1], [0, 0]])


class TestMaybeDowncast:
    def test_exact_integers(self) -> None:
        arr = np.array([1.0, 2.0, 3.0])
        result = maybe_downcast(arr, 1e-14)
        assert isinstance(result.tolist()[0], int)
        assert result.tolist() == [1, 2, 3]

    def test_near_integers_within_ct(self) -> None:
        arr = np.array([1.0000000000000002, 2.0])
        result = maybe_downcast(arr, 1e-14)
        assert isinstance(result.tolist()[0], int)

    def test_non_integers_stay_float(self) -> None:
        arr = np.array([1.5, 2.7])
        result = maybe_downcast(arr, 1e-14)
        assert isinstance(result.tolist()[0], float)

    def test_mixed_stay_float(self) -> None:
        arr = np.array([1.0, 2.5])
        result = maybe_downcast(arr, 1e-14)
        assert isinstance(result.tolist()[0], float)

    def test_already_int_unchanged(self) -> None:
        arr = np.array([1, 2, 3], dtype=np.int32)
        result = maybe_downcast(arr, 1e-14)
        assert result.tolist() == [1, 2, 3]
        assert isinstance(result.tolist()[0], int)

    def test_large_whole_integers_stay_float(self) -> None:
        arr = np.array([1e18])
        result = maybe_downcast(arr, 1e-14)
        assert result.tolist()[0] == 1e18

    def test_zero_ct_exact_only(self) -> None:
        arr = np.array([1.0000000000000002])
        result = maybe_downcast(arr, 0)
        assert isinstance(result.tolist()[0], float)

    def test_zero_ct_exact_integers(self) -> None:
        arr = np.array([1.0, 2.0])
        result = maybe_downcast(arr, 0)
        assert isinstance(result.tolist()[0], int)

    def test_empty_unchanged(self) -> None:
        arr = np.array([])
        result = maybe_downcast(arr, 1e-14)
        assert result.tolist() == []



class TestMaybeUpcast:
    def test_int_becomes_float(self) -> None:
        arr = np.array([1, 2, 3], dtype=np.int32)
        result = maybe_upcast(arr)
        assert isinstance(result.tolist()[0], float)

    def test_float_unchanged(self) -> None:
        arr = np.array([1.5, 2.5])
        result = maybe_upcast(arr)
        assert result.tolist() == [1.5, 2.5]

    def test_values_preserved(self) -> None:
        arr = np.array([1, 2, 3], dtype=np.int32)
        result = maybe_upcast(arr)
        assert result.tolist() == [1.0, 2.0, 3.0]

