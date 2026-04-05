"""Operator bindings (reduce, scan) for MARPLE."""

from typing import Any, Callable

from marple.numpy_array import APLArray, S
from marple.backend_functions import to_list
from marple.dyadic_functions import DyadicFunctionBinding
from marple.errors import DomainError
from marple.get_numpy import np
from marple.parser import FunctionRef


# Glyph-keyed maps for reduce/scan

_IDENTITY_ELEMENTS: dict[str, int | float] = {
    "+": 0,
    "-": 0,
    "×": 1,
    "÷": 1,
    "⌈": float("-inf"),
    "⌊": float("inf"),
    "∧": 1,
    "∨": 0,
    "=": 1,
    "≠": 0,
    "<": 0,
    "≤": 1,
    ">": 0,
    "≥": 1,
}


def _reduce_vector(
    func: Callable[[APLArray, APLArray], APLArray],
    data: list[Any],
) -> Any:
    """Reduce a flat list right-to-left, returning a scalar value."""
    result = S(data[-1])
    for i in range(len(data) - 2, -1, -1):
        result = func(S(data[i]), result)
    return result.data[0]


def _reduce(
    func: Callable[[APLArray, APLArray], APLArray],
    omega: APLArray,
    glyph: str | None = None,
) -> APLArray:
    """Reduce along the last axis."""
    data = omega.data
    if len(data) == 0:
        if glyph is not None:
            identity = _IDENTITY_ELEMENTS.get(glyph)
            if identity is not None:
                return S(identity)
        raise DomainError("Cannot reduce empty array")
    if len(omega.shape) <= 1:
        return S(_reduce_vector(func, to_list(data)))
    last = omega.shape[-1]
    new_shape = omega.shape[:-1]
    data_list = to_list(data)
    n_rows = len(data_list) // last
    results: list[Any] = []
    for i in range(n_rows):
        row = data_list[i * last : (i + 1) * last]
        results.append(_reduce_vector(func, row))
    return APLArray.array(new_shape, results)


_ACCUMULATE_UFUNCS: dict[str, Any] = {
    "+": np.add,
    "×": np.multiply,
    "⌈": np.maximum,
    "⌊": np.minimum,
}

_SCALAR_OPS: dict[str, Any] = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "×": lambda a, b: a * b,
    "÷": lambda a, b: a / b,
    "⌈": lambda a, b: max(a, b),
    "⌊": lambda a, b: min(a, b),
    "*": lambda a, b: a ** b,
    "⍟": lambda a, b: np.log(b) / np.log(a),
    "|": lambda a, b: b % a,
    "∧": lambda a, b: int(bool(a) and bool(b)),
    "∨": lambda a, b: int(bool(a) or bool(b)),
    "≠": lambda a, b: int(a != b),
    "=": lambda a, b: int(a == b),
    "<": lambda a, b: int(a < b),
    "≤": lambda a, b: int(a <= b),
    ">": lambda a, b: int(a > b),
    "≥": lambda a, b: int(a >= b),
}


def _scan_row_accumulate(ufunc: Any, data: Any, row_len: int) -> Any:
    """Apply ufunc.accumulate to each row of length row_len in flat data."""
    n = len(data)
    result = np.empty(n, dtype=data.dtype)
    for i in range(0, n, row_len):
        result[i:i + row_len] = ufunc.accumulate(data[i:i + row_len])
    return result


def _scan_row_general(op: Any, data: Any, row_len: int) -> Any:
    """O(n²) right-to-left reduce per prefix, row by row."""
    n = len(data)
    result = np.empty(n, dtype=np.float64)
    for i in range(0, n, row_len):
        row = data[i:i + row_len]
        result[i] = row[0]
        for k in range(1, row_len):
            acc = row[k]
            for j in range(k - 1, -1, -1):
                acc = op(row[j], acc)
            result[i + k] = acc
    return result


def _scan(
    func: Callable[[APLArray, APLArray], APLArray],
    omega: APLArray,
    glyph: str | None = None,
) -> APLArray:
    """Scan along the last axis."""
    data = omega.data
    n = len(data)
    if n == 0:
        return APLArray.array([0], [])
    row_len = omega.shape[-1] if len(omega.shape) > 0 else n
    # Fast path: commutative ops use numpy accumulate
    if glyph is not None:
        ufunc = _ACCUMULATE_UFUNCS.get(glyph)
        if ufunc is not None:
            return APLArray.array(list(omega.shape), _scan_row_accumulate(ufunc, data, row_len))
    # General path: O(n²) right-to-left reduce per prefix
    op = _SCALAR_OPS.get(glyph) if glyph is not None else None
    if op is not None:
        return APLArray.array(list(omega.shape), _scan_row_general(op, data, row_len))
    raise DomainError(f"Unknown function for scan: {glyph}")


def _reduce_first(
    func: Callable[[APLArray, APLArray], APLArray],
    omega: APLArray,
    glyph: str | None = None,
) -> APLArray:
    """Reduce along the first axis (⌿)."""
    if len(omega.shape) <= 1:
        return _reduce(func, omega, glyph)
    first = omega.shape[0]
    cell_shape = omega.shape[1:]
    cell_size = 1
    for s in cell_shape:
        cell_size *= s
    data_list = to_list(omega.data)
    acc = data_list[:cell_size]
    for i in range(1, first):
        cell = data_list[i * cell_size : (i + 1) * cell_size]
        paired = []
        for a, b in zip(acc, cell):
            paired.append(func(S(a), S(b)).data[0])
        acc = paired
    return APLArray.array(cell_shape, acc)


def _scan_first(
    func: Callable[[APLArray, APLArray], APLArray],
    omega: APLArray,
    glyph: str | None = None,
) -> APLArray:
    """Scan along the first axis (⍀)."""
    if len(omega.shape) <= 1:
        return _scan(func, omega, glyph)
    first = omega.shape[0]
    cell_shape = omega.shape[1:]
    cell_size = 1
    for s in cell_shape:
        cell_size *= s
    data_list = to_list(omega.data)
    acc = data_list[:cell_size]
    results = list(acc)
    for i in range(1, first):
        cell = data_list[i * cell_size : (i + 1) * cell_size]
        new_acc = []
        for a, b in zip(acc, cell):
            new_acc.append(func(S(a), S(b)).data[0])
        acc = new_acc
        results.extend(acc)
    return APLArray.array(list(omega.shape), results)


_OPERATOR_DISPATCH: dict[str, Any] = {
    "/": _reduce,
    "⌿": _reduce_first,
    "\\": _scan,
    "⍀": _scan_first,
}


class DerivedFunctionBinding:
    """A derived function: an operator applied to a function operand."""

    def apply(self, operator: str, function: object, operand: APLArray) -> APLArray:
        """Apply the derived function (operator + function) to an operand."""
        func, glyph = self._resolve_function(function)
        op_fn = _OPERATOR_DISPATCH.get(operator)
        if op_fn is None:
            raise DomainError(f"Unknown operator: {operator}")
        return op_fn(func, operand, glyph)

    def _resolve_function(self, function: object) -> tuple[Any, str | None]:
        """Resolve a function node to (dyadic callable, glyph or None)."""
        if isinstance(function, str):
            return DyadicFunctionBinding.resolve(function), function
        if isinstance(function, FunctionRef):
            return DyadicFunctionBinding.resolve(function.glyph), function.glyph
        raise DomainError("Operators require primitive function operands")
