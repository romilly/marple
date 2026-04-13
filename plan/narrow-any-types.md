# Plan: Narrow `Any` Type Annotations

## Context

After wrapping raw strings on the parser stack (v0.8.12), we're now narrowing `Any` type annotations across the codebase. Most `Any` usages fall into three categories: callable lambdas in dispatch dicts, numpy array data, and environment/symbol-table storage. Many can be replaced with concrete types now that the type hierarchy is cleaner.

## Approach

Work file-by-file, running pytest + pyright after each file. This is pure refactoring -- no behaviour changes.

## Files and changes

### 1. `src/marple/nodes.py`

| Line | Current | Narrow to |
|------|---------|-----------|
| 14 | `_INNER_SCALAR_OPS: dict[str, Any]` | `dict[str, Callable[[Any, Any], Any]]` |
| 88 | `_OUTER_UFUNCS: dict[str, Any]` | `dict[str, str]` (values are numpy ufunc name strings) |

### 2. `src/marple/backend_functions.py`

Many functions accept/return `Any` where `np.ndarray[Any, Any]` (alias `NDArray`) would be correct. However, several deliberately accept mixed types (ndarray OR plain list OR scalar) as a duck-typing boundary -- narrowing those would require overloads or unions.

Safe to narrow:

| Line | Current | Narrow to |
|------|---------|-----------|
| 16 | `str_to_char_array(s) -> Any` | `-> NDArray[np.uint32]` |
| 21 | `char_fill() -> Any` | `-> np.uint32` |
| 26 | `to_array(...) -> Any` | `-> NDArray[Any]` |
| 91 | `_is_int_dtype(arr: Any)` | `arr: NDArray[Any]` |
| 97 | `_is_float_dtype(arr: Any)` | `arr: NDArray[Any]` |
| 181 | `to_bool_array(data: Any) -> Any` | `-> NDArray[np.uint8]` |

Keep as `Any` (duck-typing boundaries -- accept ndarray, list, or scalar):
- `is_char_array`, `chars_to_str`, `is_ndarray`, `is_numeric_array` -- type-guard predicates that must accept anything
- `maybe_upcast`, `maybe_downcast`, `data_type_code` -- accept and return ndarray but also pass through non-ndarray unchanged
- `_to_python`, `to_list` -- deliberately polymorphic
- `format_num` -- accepts numpy scalar or Python numeric

### 3. `src/marple/operator_binding.py`

| Line | Current | Narrow to |
|------|---------|-----------|
| 107 | `_ACCUMULATE_UFUNCS: dict[str, Any]` | `dict[str, np.ufunc]` |
| 116 | `_SCALAR_OPS: dict[str, Any]` | `dict[str, Callable[[Any, Any], Any]]` |
| 288 | `_OPERATOR_DISPATCH: dict[str, Any]` | `dict[str, Callable[..., APLArray]]` |
| 51 | `_reduce_row(op: Any, data: Any, ...) -> Any` | `op: Callable[[Any, Any], Any], data: NDArray[Any], -> Any` |
| 137 | `_scan_row_accumulate(ufunc: Any, data: Any, ...) -> Any` | `ufunc: np.ufunc, data: NDArray[Any], -> NDArray[Any]` |
| 146 | `_scan_row_general(op: Any, data: Any, ...) -> Any` | `op: Callable[[Any, Any], Any], data: NDArray[Any], -> NDArray[Any]` |
| 182, 228, 266 | nested `_do_scan/_do_reduce(data: Any) -> Any` | `data: NDArray[Any], -> NDArray[Any]` |

### 4. `src/marple/numpy_array.py`

| Line | Current | Narrow to |
|------|---------|-----------|
| 83 | `_dyadic(self, other, f: Any, ...)` | `f: Callable[[Any, Any], Any]` |
| 109 | `_numeric_dyadic_op(self, other, op: Any, ...)` | `op: Callable[[Any, Any], Any]` |
| 207 | `_CIRCULAR: dict[int, Any]` | `dict[int, Callable[[float], float]]` |
| 237 | `_compare(self, other, op: Any, ...)` | `op: Callable[[Any, Any, Any], Any]` |
| 516 | `S(value: Any)` | `value: int | float | str | np.integer[Any] | np.floating[Any]` |

Keep as `Any`:
- `__init__(self, shape, data: Any)` -- accepts list, ndarray, scalar; complex union not worth it
- `array(cls, shape, data: Any)` -- same reason
- `scalar(cls, value: Any)` -- same reason (though `S()` is narrowed since it's the public API)
- `_apply`, `_binom`, `_tolerant_eq` -- scalar lambdas where numpy generics make the union unwieldy

### 5. `src/marple/formatting.py`

| Line | Current | Narrow to |
|------|---------|-----------|
| 60 | `format_result(result, env: Any = None)` | `env: 'Environment | None' = None` |

Keep `format_num(x: Any)` -- accepts numpy scalar, Python int/float/bool.

### 6. `src/marple/environment.py`

| Line | Current | Narrow to |
|------|---------|-----------|
| 37 | `self._locals: dict[str, Any]` | `dict[str, APLValue]` -- but only if DfnBinding inherits APLValue. Need to check. If not, keep `Any`. |

The dict-like interface methods (`__setitem__`, `get`, `setdefault`, `pop`, `items`) follow from `_locals` type -- they narrow automatically if `_locals` narrows.

### 7. `src/marple/symbol_table.py`

| Line | Current | Narrow to |
|------|---------|-----------|
| 24 | `self._values: dict[str, Any]` | `dict[str, APLValue]` -- same caveat as environment |
| 29 | `bind(self, name, value: Any, ...)` | `value: APLValue` |
| 38 | `get(self, name) -> Any` | `-> APLValue | None` |

### 8. `src/marple/namespace.py`

| Line | Current | Narrow to |
|------|---------|-----------|
| 12 | `self.entries: dict[str, Any]` | `dict[str, Namespace | APLValue]` |
| 14 | `resolve(...) -> Any` | `-> Namespace | APLValue | None` |
| 28 | `register(name, value: Any)` | `value: Namespace | APLValue` |

## Order of work

1. `nodes.py` -- two dict type annotations
2. `backend_functions.py` -- return types and private function params
3. `operator_binding.py` -- dispatch dicts and function params
4. `numpy_array.py` -- callable params and `_CIRCULAR` dict
5. `formatting.py` -- `env` parameter
6. Check if `_locals`/symbol table can narrow to `APLValue` (depends on what DfnBinding is)
7. `symbol_table.py` + `environment.py` + `namespace.py` if feasible
8. Bump version

## Verification

- `pytest` -- 1338 tests pass after each file
- `pyright src/` -- zero errors after each file
