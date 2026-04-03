
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
            return APLArray.array(list(omega.shape), result)
    data = [f(x) for x in to_list(omega.data)]
    if bool_result:
        data = to_bool_array(data)
    return APLArray.array(list(omega.shape), data)


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
            return APLArray.array(shape, result)
    # Fallback: element-wise Python
    a_data = to_list(alpha.data)
    b_data = to_list(omega.data)
    if alpha.is_scalar() and omega.is_scalar():
        result = [f(a_data[0], b_data[0])]
        if bool_result:
            result = to_bool_array(result)
        return APLArray.array([], result)
    if alpha.is_scalar():
        a = a_data[0]
        data = to_bool_array([f(a, x) for x in b_data]) if bool_result else [f(a, x) for x in b_data]
        return APLArray.array(list(omega.shape), data)
    if omega.is_scalar():
        b = b_data[0]
        data = to_bool_array([f(x, b) for x in a_data]) if bool_result else [f(x, b) for x in a_data]
        return APLArray.array(list(alpha.shape), data)
    if alpha.shape != omega.shape:
        raise LengthError(f"Shape mismatch: {alpha.shape} vs {omega.shape}")
    data = [f(a, b) for a, b in zip(a_data, b_data)]
    if bool_result:
        data = to_bool_array(data)
    return APLArray.array(list(alpha.shape), data)


# Monadic functions


# Dyadic functions — thin wrappers for operator_binding compatibility

def add(alpha: APLArray, omega: APLArray) -> APLArray:
    return alpha.add(omega)

def subtract(alpha: APLArray, omega: APLArray) -> APLArray:
    return alpha.subtract(omega)

def multiply(alpha: APLArray, omega: APLArray) -> APLArray:
    return alpha.multiply(omega)

def divide(alpha: APLArray, omega: APLArray) -> APLArray:
    return alpha.divide(omega)

def maximum(alpha: APLArray, omega: APLArray) -> APLArray:
    return alpha.maximum(omega)

def minimum(alpha: APLArray, omega: APLArray) -> APLArray:
    return alpha.minimum(omega)


def binomial(alpha: APLArray, omega: APLArray) -> APLArray:
    return alpha.binomial(omega)

def circular(alpha: APLArray, omega: APLArray) -> APLArray:
    return alpha.circular(omega)

def power(alpha: APLArray, omega: APLArray) -> APLArray:
    return alpha.power(omega)

def logarithm(alpha: APLArray, omega: APLArray) -> APLArray:
    return alpha.logarithm(omega)

def residue(alpha: APLArray, omega: APLArray) -> APLArray:
    return alpha.residue(omega)


def less_than(alpha: APLArray, omega: APLArray, ct: float = 0) -> APLArray:
    return alpha.less_than(omega, ct)

def less_equal(alpha: APLArray, omega: APLArray, ct: float = 0) -> APLArray:
    return alpha.less_equal(omega, ct)

def equal(alpha: APLArray, omega: APLArray, ct: float = 0) -> APLArray:
    return alpha.equal(omega, ct)

def greater_equal(alpha: APLArray, omega: APLArray, ct: float = 0) -> APLArray:
    return alpha.greater_equal(omega, ct)

def greater_than(alpha: APLArray, omega: APLArray, ct: float = 0) -> APLArray:
    return alpha.greater_than(omega, ct)

def not_equal(alpha: APLArray, omega: APLArray, ct: float = 0) -> APLArray:
    return alpha.not_equal(omega, ct)


def logical_and(alpha: APLArray, omega: APLArray) -> APLArray:
    return _pervade_dyadic(lambda a, b: int(bool(a) and bool(b)), alpha, omega, "logical_and", bool_result=True)


def logical_or(alpha: APLArray, omega: APLArray) -> APLArray:
    return _pervade_dyadic(lambda a, b: int(bool(a) or bool(b)), alpha, omega, "logical_or", bool_result=True)
