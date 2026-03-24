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
