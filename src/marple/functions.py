
import math
try:
    from typing import Callable
except ImportError:
    pass

from marple.arraymodel import APLArray
from marple.backend import (
    _DOWNCAST_CT, _OVERFLOW_UFUNCS, is_numeric_array,
    maybe_downcast, maybe_upcast, np, to_bool_array, to_list,
)
from marple.errors import DomainError, LengthError


def _pervade_monadic(
    f: Callable[[int | float], int | float],
    omega: APLArray,
    ufunc_name: str | None = None,
    bool_result: bool = False,
) -> APLArray:
    if ufunc_name and is_numeric_array(omega.data):
        ufunc = getattr(np, ufunc_name, None)
        if ufunc is not None:
            result = ufunc(omega.data)
            if bool_result:
                result = to_bool_array(result)
            return APLArray(list(omega.shape), result)
    data = [f(x) for x in to_list(omega.data)]
    if bool_result:
        data = to_bool_array(data)
    return APLArray(list(omega.shape), data)


def _pervade_dyadic(
    f: Callable[[int | float, int | float], int | float],
    alpha: APLArray,
    omega: APLArray,
    ufunc_name: str | None = None,
    bool_result: bool = False,
) -> APLArray:
    if (
        ufunc_name
        and is_numeric_array(alpha.data)
        and is_numeric_array(omega.data)
    ):
        ufunc = getattr(np, ufunc_name, None)
        if ufunc is not None:
            a_arr = alpha.data
            b_arr = omega.data
            if ufunc_name in _OVERFLOW_UFUNCS:
                a_arr = maybe_upcast(a_arr)
                b_arr = maybe_upcast(b_arr)
            try:
                result = ufunc(a_arr, b_arr)
            except ValueError:
                raise LengthError(f"Shape mismatch: {alpha.shape} vs {omega.shape}")
            # No downcast here — deferred to assignment/display
            if bool_result:
                result = to_bool_array(result)
            shape = list(omega.shape) if not omega.is_scalar() else list(alpha.shape)
            return APLArray(shape, result)
    # Fallback: element-wise Python
    a_data = to_list(alpha.data)
    b_data = to_list(omega.data)
    if alpha.is_scalar() and omega.is_scalar():
        return APLArray([], [f(a_data[0], b_data[0])])
    if alpha.is_scalar():
        a = a_data[0]
        data = to_bool_array([f(a, x) for x in b_data]) if bool_result else [f(a, x) for x in b_data]
        return APLArray(list(omega.shape), data)
    if omega.is_scalar():
        b = b_data[0]
        data = to_bool_array([f(x, b) for x in a_data]) if bool_result else [f(x, b) for x in a_data]
        return APLArray(list(alpha.shape), data)
    if alpha.shape != omega.shape:
        raise LengthError(f"Shape mismatch: {alpha.shape} vs {omega.shape}")
    data = [f(a, b) for a, b in zip(a_data, b_data)]
    if bool_result:
        data = to_bool_array(data)
    return APLArray(list(alpha.shape), data)


# Monadic functions

def negate(omega: APLArray) -> APLArray:
    return _pervade_monadic(lambda x: -x, omega, "negative")


def reciprocal(omega: APLArray) -> APLArray:
    def _recip(x: int | float) -> int | float:
        if x == 0:
            raise DomainError("Division by zero")
        return 1 / x
    return _pervade_monadic(_recip, omega)


def ceiling(omega: APLArray) -> APLArray:
    return _pervade_monadic(lambda x: math.ceil(x), omega, "ceil")


def floor(omega: APLArray) -> APLArray:
    return _pervade_monadic(lambda x: math.floor(x), omega, "floor")


# Dyadic functions

def add(alpha: APLArray, omega: APLArray) -> APLArray:
    return _pervade_dyadic(lambda a, b: a + b, alpha, omega, "add")


def subtract(alpha: APLArray, omega: APLArray) -> APLArray:
    return _pervade_dyadic(lambda a, b: a - b, alpha, omega, "subtract")


def multiply(alpha: APLArray, omega: APLArray) -> APLArray:
    return _pervade_dyadic(lambda a, b: a * b, alpha, omega, "multiply")


def divide(alpha: APLArray, omega: APLArray) -> APLArray:
    def _div(a: int | float, b: int | float) -> int | float:
        if b == 0:
            raise DomainError("Division by zero")
        return a / b
    return _pervade_dyadic(_div, alpha, omega)


def maximum(alpha: APLArray, omega: APLArray) -> APLArray:
    return _pervade_dyadic(lambda a, b: max(a, b), alpha, omega, "maximum")


def minimum(alpha: APLArray, omega: APLArray) -> APLArray:
    return _pervade_dyadic(lambda a, b: min(a, b), alpha, omega, "minimum")


# Extended monadic functions

def exponential(omega: APLArray) -> APLArray:
    return _pervade_monadic(lambda x: math.exp(x), omega, "exp")


def natural_log(omega: APLArray) -> APLArray:
    return _pervade_monadic(lambda x: math.log(x), omega, "log")


def absolute_value(omega: APLArray) -> APLArray:
    return _pervade_monadic(lambda x: abs(x), omega, "absolute")


def logical_not(omega: APLArray) -> APLArray:
    return _pervade_monadic(lambda x: int(not x), omega, "logical_not", bool_result=True)


def pi_times(omega: APLArray) -> APLArray:
    return _pervade_monadic(lambda x: math.pi * x, omega)


_CIRCULAR: dict[int, Callable[[float], float]] = {
    0: lambda x: math.sqrt(1 - x * x),
    1: math.sin,
    2: math.cos,
    3: math.tan,
    4: lambda x: math.sqrt(1 + x * x),
    5: math.sinh,
    6: math.cosh,
    7: math.tanh,
    -1: math.asin,
    -2: math.acos,
    -3: math.atan,
    -4: lambda x: math.sqrt(x * x - 1),
    -5: math.asinh,
    -6: math.acosh,
    -7: math.atanh,
}


def circular(alpha: APLArray, omega: APLArray) -> APLArray:
    def _apply(a: int | float, b: int | float) -> int | float:
        fn = _CIRCULAR.get(int(a))
        if fn is None:
            raise DomainError(f"Unknown circular function selector: {a}")
        return fn(float(b))
    return _pervade_dyadic(_apply, alpha, omega)


# Extended dyadic functions

def power(alpha: APLArray, omega: APLArray) -> APLArray:
    return _pervade_dyadic(lambda a, b: a ** b, alpha, omega, "power")


def logarithm(alpha: APLArray, omega: APLArray) -> APLArray:
    return _pervade_dyadic(lambda a, b: math.log(b) / math.log(a), alpha, omega)


def residue(alpha: APLArray, omega: APLArray) -> APLArray:
    return _pervade_dyadic(lambda a, b: b % a, alpha, omega)


def _tolerant_eq(a: int | float, b: int | float, ct: float) -> bool:
    """APL tolerant equality: |a-b| ≤ ct × (|a| ⌈ |b|)"""
    if ct == 0:
        return a == b
    return abs(a - b) <= ct * max(abs(a), abs(b))


def less_than(alpha: APLArray, omega: APLArray, ct: float = 0) -> APLArray:
    return _pervade_dyadic(lambda a, b: int(a < b and not _tolerant_eq(a, b, ct)), alpha, omega, bool_result=True)


def less_equal(alpha: APLArray, omega: APLArray, ct: float = 0) -> APLArray:
    return _pervade_dyadic(lambda a, b: int(a <= b or _tolerant_eq(a, b, ct)), alpha, omega, bool_result=True)


def equal(alpha: APLArray, omega: APLArray, ct: float = 0) -> APLArray:
    return _pervade_dyadic(lambda a, b: int(_tolerant_eq(a, b, ct)), alpha, omega, bool_result=True)


def greater_equal(alpha: APLArray, omega: APLArray, ct: float = 0) -> APLArray:
    return _pervade_dyadic(lambda a, b: int(a >= b or _tolerant_eq(a, b, ct)), alpha, omega, bool_result=True)


def greater_than(alpha: APLArray, omega: APLArray, ct: float = 0) -> APLArray:
    return _pervade_dyadic(lambda a, b: int(a > b and not _tolerant_eq(a, b, ct)), alpha, omega, bool_result=True)


def not_equal(alpha: APLArray, omega: APLArray, ct: float = 0) -> APLArray:
    return _pervade_dyadic(lambda a, b: int(not _tolerant_eq(a, b, ct)), alpha, omega, bool_result=True)


def logical_and(alpha: APLArray, omega: APLArray) -> APLArray:
    return _pervade_dyadic(lambda a, b: int(bool(a) and bool(b)), alpha, omega, "logical_and", bool_result=True)


def logical_or(alpha: APLArray, omega: APLArray) -> APLArray:
    return _pervade_dyadic(lambda a, b: int(bool(a) or bool(b)), alpha, omega, "logical_or", bool_result=True)
