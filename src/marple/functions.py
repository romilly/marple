from __future__ import annotations

import math
from typing import Callable

from marple.arraymodel import APLArray


def _pervade_monadic(
    f: Callable[[int | float], int | float],
    omega: APLArray,
) -> APLArray:
    return APLArray(list(omega.shape), [f(x) for x in omega.data])


def _pervade_dyadic(
    f: Callable[[int | float, int | float], int | float],
    alpha: APLArray,
    omega: APLArray,
) -> APLArray:
    if alpha.is_scalar() and omega.is_scalar():
        return APLArray([], [f(alpha.data[0], omega.data[0])])
    if alpha.is_scalar():
        a = alpha.data[0]
        return APLArray(list(omega.shape), [f(a, x) for x in omega.data])
    if omega.is_scalar():
        b = omega.data[0]
        return APLArray(list(alpha.shape), [f(x, b) for x in alpha.data])
    if alpha.shape != omega.shape:
        raise ValueError(f"Shape mismatch: {alpha.shape} vs {omega.shape}")
    return APLArray(
        list(alpha.shape),
        [f(a, b) for a, b in zip(alpha.data, omega.data)],
    )


# Monadic functions

def negate(omega: APLArray) -> APLArray:
    return _pervade_monadic(lambda x: -x, omega)


def reciprocal(omega: APLArray) -> APLArray:
    return _pervade_monadic(lambda x: 1 / x, omega)


def ceiling(omega: APLArray) -> APLArray:
    return _pervade_monadic(lambda x: math.ceil(x), omega)


def floor(omega: APLArray) -> APLArray:
    return _pervade_monadic(lambda x: math.floor(x), omega)


# Dyadic functions

def add(alpha: APLArray, omega: APLArray) -> APLArray:
    return _pervade_dyadic(lambda a, b: a + b, alpha, omega)


def subtract(alpha: APLArray, omega: APLArray) -> APLArray:
    return _pervade_dyadic(lambda a, b: a - b, alpha, omega)


def multiply(alpha: APLArray, omega: APLArray) -> APLArray:
    return _pervade_dyadic(lambda a, b: a * b, alpha, omega)


def divide(alpha: APLArray, omega: APLArray) -> APLArray:
    return _pervade_dyadic(lambda a, b: a / b, alpha, omega)


def maximum(alpha: APLArray, omega: APLArray) -> APLArray:
    return _pervade_dyadic(lambda a, b: max(a, b), alpha, omega)


def minimum(alpha: APLArray, omega: APLArray) -> APLArray:
    return _pervade_dyadic(lambda a, b: min(a, b), alpha, omega)


# Extended monadic functions

def exponential(omega: APLArray) -> APLArray:
    return _pervade_monadic(lambda x: math.exp(x), omega)


def natural_log(omega: APLArray) -> APLArray:
    return _pervade_monadic(lambda x: math.log(x), omega)


def absolute_value(omega: APLArray) -> APLArray:
    return _pervade_monadic(lambda x: abs(x), omega)


def logical_not(omega: APLArray) -> APLArray:
    return _pervade_monadic(lambda x: int(not x), omega)


def pi_times(omega: APLArray) -> APLArray:
    return _pervade_monadic(lambda x: math.pi * x, omega)


# Extended dyadic functions

def power(alpha: APLArray, omega: APLArray) -> APLArray:
    return _pervade_dyadic(lambda a, b: a ** b, alpha, omega)


def logarithm(alpha: APLArray, omega: APLArray) -> APLArray:
    return _pervade_dyadic(lambda a, b: math.log(b) / math.log(a), alpha, omega)


def residue(alpha: APLArray, omega: APLArray) -> APLArray:
    return _pervade_dyadic(lambda a, b: b % a, alpha, omega)


def less_than(alpha: APLArray, omega: APLArray) -> APLArray:
    return _pervade_dyadic(lambda a, b: int(a < b), alpha, omega)


def less_equal(alpha: APLArray, omega: APLArray) -> APLArray:
    return _pervade_dyadic(lambda a, b: int(a <= b), alpha, omega)


def equal(alpha: APLArray, omega: APLArray) -> APLArray:
    return _pervade_dyadic(lambda a, b: int(a == b), alpha, omega)


def greater_equal(alpha: APLArray, omega: APLArray) -> APLArray:
    return _pervade_dyadic(lambda a, b: int(a >= b), alpha, omega)


def greater_than(alpha: APLArray, omega: APLArray) -> APLArray:
    return _pervade_dyadic(lambda a, b: int(a > b), alpha, omega)


def not_equal(alpha: APLArray, omega: APLArray) -> APLArray:
    return _pervade_dyadic(lambda a, b: int(a != b), alpha, omega)


def logical_and(alpha: APLArray, omega: APLArray) -> APLArray:
    return _pervade_dyadic(lambda a, b: int(bool(a) and bool(b)), alpha, omega)


def logical_or(alpha: APLArray, omega: APLArray) -> APLArray:
    return _pervade_dyadic(lambda a, b: int(bool(a) or bool(b)), alpha, omega)
