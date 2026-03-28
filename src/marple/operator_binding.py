"""Operator bindings (reduce, scan) for MARPLE."""

from typing import Any, Callable

from marple.arraymodel import APLArray, S
from marple.backend import is_numeric_array, maybe_upcast, np, to_list
from marple.dyadic_functions import DyadicFunctionBinding
from marple.errors import DomainError
from marple.functions import add, multiply, maximum, minimum
from marple.parser import FunctionRef


# Map function objects to numpy ufunc names for fast reduce
_UFUNC_MAP: dict[object, str] = {
    add: "add",
    multiply: "multiply",
    maximum: "maximum",
    minimum: "minimum",
}

_COMMUTATIVE = {add, multiply, maximum, minimum}


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
) -> APLArray:
    """Reduce along the last axis."""
    data = omega.data
    if len(data) == 0:
        raise DomainError("Cannot reduce empty array")
    if func in _COMMUTATIVE:
        ufunc_name = _UFUNC_MAP.get(func)
        if ufunc_name and is_numeric_array(data):
            ufunc = getattr(np, ufunc_name, None)
            if ufunc is not None and hasattr(ufunc, "reduce"):
                work_data = maybe_upcast(data)
                if len(omega.shape) <= 1:
                    return S(ufunc.reduce(work_data).item())
                shaped = np.reshape(work_data, omega.shape)
                result = ufunc.reduce(shaped, axis=-1)
                return APLArray(list(result.shape), result.ravel())
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
    return APLArray(new_shape, results)


def _scan(
    func: Callable[[APLArray, APLArray], APLArray],
    omega: APLArray,
) -> APLArray:
    """Scan along the last axis."""
    if len(omega.shape) <= 1:
        data = omega.data
        if len(data) == 0:
            return APLArray([0], [])
        results = [data[0]]
        acc = S(data[0])
        for i in range(1, len(data)):
            acc = func(acc, S(data[i]))
            results.append(acc.data[0])
        return APLArray([len(results)], results)
    last = omega.shape[-1]
    n_rows = len(omega.data) // last
    results: list[Any] = []
    for i in range(n_rows):
        row = omega.data[i * last : (i + 1) * last]
        acc = S(row[0])
        results.append(row[0])
        for j in range(1, last):
            acc = func(acc, S(row[j]))
            results.append(acc.data[0])
    return APLArray(list(omega.shape), results)


def _reduce_first(
    func: Callable[[APLArray, APLArray], APLArray],
    omega: APLArray,
) -> APLArray:
    """Reduce along the first axis (⌿)."""
    if len(omega.shape) <= 1:
        return _reduce(func, omega)
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
    return APLArray(cell_shape, acc)


def _scan_first(
    func: Callable[[APLArray, APLArray], APLArray],
    omega: APLArray,
) -> APLArray:
    """Scan along the first axis (⍀)."""
    if len(omega.shape) <= 1:
        return _scan(func, omega)
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
    return APLArray(list(omega.shape), results)


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
        func = self._resolve_function(function)
        op_fn = _OPERATOR_DISPATCH.get(operator)
        if op_fn is None:
            raise DomainError(f"Unknown operator: {operator}")
        return op_fn(func, operand)

    def _resolve_function(self, function: object) -> Any:
        """Resolve a function node to a dyadic callable."""
        if isinstance(function, str):
            return DyadicFunctionBinding.resolve(function)
        if isinstance(function, FunctionRef):
            return DyadicFunctionBinding.resolve(function.glyph)
        raise DomainError(f"Expected function for operator, got {type(function)}")
