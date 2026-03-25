"""Tests for numeric type upcast/downcast infrastructure."""

import pytest

from marple.arraymodel import S
from marple.backend import HAS_BACKEND, maybe_downcast, maybe_upcast, np
from marple.interpreter import interpret, default_env

needs_backend = pytest.mark.skipif(not HAS_BACKEND, reason="no numpy backend")


@needs_backend
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
        # 1e18 is a whole number but exceeds int32 range — stays as float array
        arr = np.array([1e18])
        result = maybe_downcast(arr, 1e-14)
        # to_array can't fit it in int32/int16, so it becomes float
        assert result.tolist()[0] == 1e18

    def test_zero_ct_exact_only(self) -> None:
        arr = np.array([1.0000000000000002])
        result = maybe_downcast(arr, 0)
        # Not exactly integer, so should stay float
        assert isinstance(result.tolist()[0], float)

    def test_zero_ct_exact_integers(self) -> None:
        arr = np.array([1.0, 2.0])
        result = maybe_downcast(arr, 0)
        assert isinstance(result.tolist()[0], int)

    def test_empty_unchanged(self) -> None:
        arr = np.array([])
        result = maybe_downcast(arr, 1e-14)
        assert result.tolist() == []

    def test_plain_list_unchanged(self) -> None:
        data = [1.0, 2.0]
        result = maybe_downcast(data, 1e-14)
        assert result is data


@needs_backend
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
        arr = np.array([100, 200, 300], dtype=np.int32)
        result = maybe_upcast(arr)
        assert result.tolist() == [100.0, 200.0, 300.0]

    def test_plain_list_unchanged(self) -> None:
        data = [1, 2, 3]
        result = maybe_upcast(data)
        assert result is data


@needs_backend
class TestArithmeticUpcastDowncast:
    def test_add_integers_gives_integer(self) -> None:
        result = interpret("2+3")
        assert result == S(5)
        assert isinstance(result.data.tolist()[0], int)

    def test_add_large_no_overflow(self) -> None:
        result = interpret("20000+20000")
        assert result == S(40000)

    def test_multiply_large_no_overflow(self) -> None:
        result = interpret("200×200")
        assert result == S(40000)

    def test_division_stays_float(self) -> None:
        result = interpret("1÷3")
        assert isinstance(result.data.tolist()[0], float)

    def test_add_floats_downcast_to_integer(self) -> None:
        result = interpret("1.5+1.5")
        assert result == S(3)
        assert isinstance(result.data.tolist()[0], int)


@needs_backend
class TestReduceScanOverflow:
    def test_reduce_add_overflows_int32(self) -> None:
        # 2000000000 + 2000000000 = 4000000000, overflows int32
        result = interpret("+/2000000000 2000000000")
        assert result == S(4000000000)

    def test_reduce_multiply_overflows_int32(self) -> None:
        result = interpret("×/100000 100000")
        assert result == S(10000000000)

    def test_reduce_add_small_stays_integer(self) -> None:
        result = interpret("+/1 2 3")
        assert result == S(6)
        assert isinstance(result.data.tolist()[0], int)

    def test_scan_add_overflows_int32(self) -> None:
        result = interpret("+\\2000000000 2000000000")
        expected = [2000000000, 4000000000]
        assert list(result.data) == expected


@needs_backend
class TestProductOverflow:
    def test_outer_product_overflows_int32(self) -> None:
        result = interpret("100000 200000∘.×100000 200000")
        assert list(result.data) == [10000000000, 20000000000, 20000000000, 40000000000]

    def test_outer_product_small_is_integer(self) -> None:
        result = interpret("1 2∘.+3 4")
        assert isinstance(result.data.tolist()[0], int)


@needs_backend
class TestBooleanDtype:
    def test_comparison_produces_uint8(self) -> None:
        result = interpret("1 2 3=1 3 3")
        assert str(result.data.dtype) == "uint8"

    def test_less_than_produces_uint8(self) -> None:
        result = interpret("1 2 3<2 2 2")
        assert str(result.data.dtype) == "uint8"

    def test_not_produces_uint8(self) -> None:
        result = interpret("~1 0 1")
        assert str(result.data.dtype) == "uint8"

    def test_and_produces_uint8(self) -> None:
        result = interpret("1 0 1∧1 1 0")
        assert str(result.data.dtype) == "uint8"

    def test_or_produces_uint8(self) -> None:
        result = interpret("1 0 1∨0 1 0")
        assert str(result.data.dtype) == "uint8"

    def test_boolean_values_correct(self) -> None:
        result = interpret("1 2 3=1 3 3")
        assert list(result.data) == [1, 0, 1]

    def test_boolean_in_arithmetic(self) -> None:
        result = interpret("2+(1 2 3=1 3 3)")
        assert list(result.data) == [3, 2, 3]

    def test_replicate_with_boolean(self) -> None:
        result = interpret("(3>⍳5)/⍳5")
        assert list(result.data) == [1, 2]


@needs_backend
class TestCrossDtypeArithmetic:
    """Arithmetic must work correctly across all dtype combinations:
    int, float, boolean (uint8)."""

    # ── int × int ──
    def test_int_add_int(self) -> None:
        result = interpret("1 2 3+4 5 6")
        assert list(result.data) == [5, 7, 9]
        assert isinstance(result.data.tolist()[0], int)

    def test_int_multiply_int(self) -> None:
        result = interpret("2 3×4 5")
        assert list(result.data) == [8, 15]

    def test_int_subtract_int(self) -> None:
        result = interpret("10 20-3 7")
        assert list(result.data) == [7, 13]

    # ── float × float ──
    def test_float_add_float(self) -> None:
        result = interpret("1.5 2.5+3.5 4.5")
        assert list(result.data) == [5, 7]

    def test_float_multiply_float(self) -> None:
        env = default_env()
        interpret("v←1.5 2.0", env)
        result = interpret("v×0.5 3.0", env)
        assert list(result.data) == [0.75, 6]

    # ── int × float (mixed) ──
    def test_int_add_float(self) -> None:
        result = interpret("1 2 3+0.5 0.5 0.5")
        assert list(result.data) == [1.5, 2.5, 3.5]

    def test_float_add_int(self) -> None:
        result = interpret("0.5 1.5+1 2")
        assert list(result.data) == [1.5, 3.5]

    def test_int_multiply_float(self) -> None:
        result = interpret("2 3×1.5 2.5")
        assert list(result.data) == [3, 7.5]

    # ── boolean × int ──
    def test_bool_add_int(self) -> None:
        env = default_env()
        interpret("b←1 2 3=1 3 3", env)  # b is uint8: 1 0 1
        result = interpret("b+10 20 30", env)
        assert list(result.data) == [11, 20, 31]

    def test_int_add_bool(self) -> None:
        env = default_env()
        interpret("b←1 2 3=1 3 3", env)
        result = interpret("10 20 30+b", env)
        assert list(result.data) == [11, 20, 31]

    def test_int_multiply_bool(self) -> None:
        env = default_env()
        interpret("b←1 2 3=1 3 3", env)
        result = interpret("10 20 30×b", env)
        assert list(result.data) == [10, 0, 30]

    # ── boolean × float ──
    def test_bool_add_float(self) -> None:
        env = default_env()
        interpret("b←1 2 3=1 3 3", env)
        result = interpret("b+0.5 1.5 2.5", env)
        assert list(result.data) == [1.5, 1.5, 3.5]

    def test_float_multiply_bool(self) -> None:
        env = default_env()
        interpret("b←1 2 3=1 3 3", env)
        result = interpret("3.14 2.71 1.41×b", env)
        # 3.14×1, 2.71×0, 1.41×1
        assert result.data.tolist()[1] == 0

    # ── boolean × boolean ──
    def test_bool_add_bool(self) -> None:
        env = default_env()
        interpret("a←1 0 1=1 1 1", env)  # 1 0 1
        interpret("b←1 1 0=1 1 1", env)  # 1 1 0
        result = interpret("a+b", env)
        assert list(result.data) == [2, 1, 1]

    def test_bool_multiply_bool(self) -> None:
        env = default_env()
        interpret("a←1 0 1=1 1 1", env)
        interpret("b←1 1 0=1 1 1", env)
        result = interpret("a×b", env)
        assert list(result.data) == [1, 0, 0]

    # ── scalar extension across dtypes ──
    def test_scalar_int_add_float_vector(self) -> None:
        result = interpret("10+0.5 1.5 2.5")
        assert list(result.data) == [10.5, 11.5, 12.5]

    def test_scalar_float_multiply_int_vector(self) -> None:
        result = interpret("0.5×2 4 6")
        assert list(result.data) == [1, 2, 3]

    def test_scalar_int_add_bool_vector(self) -> None:
        env = default_env()
        interpret("b←1 2 3=1 3 3", env)
        result = interpret("100+b", env)
        assert list(result.data) == [101, 100, 101]


@needs_backend
class TestCrossDtypeReduce:
    """Reduce must work across all dtypes."""

    def test_reduce_int(self) -> None:
        assert interpret("+/1 2 3 4") == S(10)

    def test_reduce_float(self) -> None:
        result = interpret("+/0.1 0.2 0.3")
        assert abs(result.data.tolist()[0] - 0.6) < 1e-10

    def test_reduce_bool(self) -> None:
        env = default_env()
        interpret("b←1 2 3 4 5>3", env)  # 0 0 0 1 1
        result = interpret("+/b", env)
        assert result == S(2)

    def test_reduce_multiply_bool(self) -> None:
        env = default_env()
        interpret("b←1 1 1=1 1 1", env)  # 1 1 1
        result = interpret("×/b", env)
        assert result == S(1)


@needs_backend
class TestCrossDtypeProducts:
    """Inner and outer products across dtypes."""

    def test_inner_product_int(self) -> None:
        assert interpret("1 2 3+.×4 5 6") == S(32)

    def test_inner_product_float(self) -> None:
        result = interpret("1.0 2.0+.×3.0 4.0")
        assert result == S(11)

    def test_inner_product_mixed(self) -> None:
        result = interpret("1 2+.×0.5 1.5")
        assert result == S(3.5)

    def test_inner_product_bool(self) -> None:
        env = default_env()
        interpret("a←1 0 1=1 1 1", env)  # 1 0 1
        interpret("b←1 1 0=1 1 1", env)  # 1 1 0
        result = interpret("a+.×b", env)
        assert result == S(1)

    def test_outer_product_int(self) -> None:
        result = interpret("1 2∘.×3 4")
        assert list(result.data) == [3, 4, 6, 8]

    def test_outer_product_float(self) -> None:
        result = interpret("0.5 1.5∘.+0.1 0.2")
        # 0.6 0.7 1.6 1.7
        vals = result.data.tolist()
        assert abs(vals[0] - 0.6) < 1e-10

    def test_outer_product_mixed(self) -> None:
        result = interpret("1 2∘.×0.5 1.5")
        assert list(result.data) == [0.5, 1.5, 1, 3]

    def test_outer_product_bool(self) -> None:
        env = default_env()
        interpret("a←1 0=1 1", env)  # 1 0
        interpret("b←0 1=1 1", env)  # 0 1
        result = interpret("a∘.∧b", env)
        assert list(result.data) == [0, 1, 0, 0]
