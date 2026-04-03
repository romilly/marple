
import os
try:
    from typing import Any
except ImportError:
    pass

# Backend selection: environment variable overrides auto-detection
try:
    _backend_name = os.environ.get("MARPLE_BACKEND", "auto")
except AttributeError:
    _backend_name = "auto"  # MicroPython has no os.environ

np: Any = None

if _backend_name != "none":
    try:
        import cupy as np  # type: ignore[no-redef]
    except ImportError:
        try:
            import numpy as np  # type: ignore[no-redef]
        except ImportError:
            try:
                import ulab.numpy as np  # type: ignore[no-redef,import-not-found]
            except ImportError:
                try:
                    from ulab import numpy as np  # type: ignore[no-redef,import-not-found]
                except ImportError:
                    np = None

HAS_BACKEND: bool = np is not None

# Module-level comparison tolerance for downcast (updated by interpreter when ⎕CT changes)
_DOWNCAST_CT: float = 1e-14

# Ufunc names that can overflow integer arithmetic


def to_array(data: list[Any]) -> Any:
    """Convert a Python list to an ndarray if numeric and backend is available."""
    if not HAS_BACKEND or len(data) == 0:
        return data
    if not all(isinstance(x, (int, float)) for x in data):
        return data
    # Preserve integer type: ulab defaults to float, so specify dtype explicitly
    if all(isinstance(x, int) for x in data):
        for dtype_name in ("int32", "int16"):
            dt = getattr(np, dtype_name, None)
            if dt is not None:
                try:
                    arr = np.array(data, dtype=dt)
                except (ValueError, OverflowError):
                    continue
                # Verify no silent overflow (numpy/ulab wrap without error)
                if arr.tolist() == data:
                    return arr
    return np.array(data)


def _to_python(x: Any) -> Any:
    """Convert a numpy scalar to a native Python type."""
    if hasattr(x, "item"):
        return x.item()  # type: ignore[union-attr]
    return x


def to_list(data: Any) -> list[Any]:
    """Convert an ndarray or list to a Python list with native types."""
    if isinstance(data, list):
        # Only convert if list might contain numpy scalars
        if data and hasattr(data[0], "item"):
            return [_to_python(x) for x in data]
        return data
    return data.tolist()  # type: ignore[union-attr]


def is_numeric_array(data: Any) -> bool:
    """Check if data is an ndarray from the active backend."""
    if not HAS_BACKEND:
        return False
    return hasattr(data, "dtype")


def to_bool_array(data: Any) -> Any:
    """Convert data to a uint8 boolean array (0/1 values).

    If no backend, returns the data unchanged.
    """
    if not HAS_BACKEND:
        return data
    dt = getattr(np, "uint8", None)
    if dt is None:
        return data
    if hasattr(data, "dtype"):
        return np.array(data.tolist(), dtype=dt)
    return np.array(data, dtype=dt)


def _is_int_dtype(arr: Any) -> bool:
    """Check if an ndarray has an integer dtype."""
    dtype_str = str(arr.dtype)
    return "int" in dtype_str


def _is_float_dtype(arr: Any) -> bool:
    """Check if an ndarray has a float dtype."""
    dtype_str = str(arr.dtype)
    return "float" in dtype_str


def maybe_upcast(data: Any) -> Any:
    """Convert integer arrays to float to prevent overflow.

    Returns non-array data unchanged.
    """
    if not is_numeric_array(data):
        return data
    if not _is_int_dtype(data):
        return data
    return data.astype(np.float64)


def maybe_downcast_scalar(value: Any, ct: float) -> Any:
    """Downcast a single float value to int if close to a whole number."""
    if not isinstance(value, float):
        return value
    r = round(value)
    diff = abs(value - r)
    mag = max(abs(value), abs(r))
    if ct == 0:
        if diff == 0:
            return r
    elif mag == 0 or diff <= ct * mag:
        return r
    return value


def maybe_downcast(data: Any, ct: float) -> Any:
    """Convert float arrays to int if all elements are close to whole numbers.

    Uses APL tolerance: |value - round(value)| <= ct * max(|value|, |round(value)|)
    Returns non-array or already-integer data unchanged.
    """
    if not is_numeric_array(data):
        return data
    if _is_int_dtype(data):
        return data
    if not _is_float_dtype(data):
        return data
    if data.size == 0:
        return data
    # Non-finite values (inf, nan) can't be downcast
    if not np.all(np.isfinite(data)):
        return data
    # Vectorised check: are all values close to whole numbers?
    rounded = np.round(data)
    diff = np.abs(data - rounded)
    if ct == 0:
        if not np.all(diff == 0):
            return data
    else:
        mag = np.maximum(np.abs(data), np.abs(rounded))
        if not np.all(diff <= ct * mag):
            return data
    # All close to integers — use int32 if values fit, else int64
    int_arr = rounded.astype(np.int64)
    if np.all(np.abs(int_arr) <= np.iinfo(np.int32).max):
        return int_arr.astype(np.int32)
    return int_arr


def data_type_code(data: Any) -> int:
    """Return the ⎕DR type code for the given data.

    Encoding: first digits = bit width, last digit = type
    (0=char, 1=boolean, 3=signed int, 5=float, 7=decimal, 9=complex).
    """
    if is_numeric_array(data):
        dtype_str = str(data.dtype)
        if "uint8" in dtype_str:
            return 81
        if "int8" in dtype_str and "int16" not in dtype_str and "int32" not in dtype_str and "int64" not in dtype_str:
            return 83
        if "int16" in dtype_str:
            return 163
        if "int32" in dtype_str:
            return 323
        if "int64" in dtype_str:
            return 643
        if _is_float_dtype(data):
            return 645
    if isinstance(data, list) and data and isinstance(data[0], str):
        return 320
    return 323


from abc import ABC, abstractmethod


class APLArray(ABC):
    """Abstract base class for APL arrays. Use factory methods array() and scalar()."""

    def __init__(self, shape: list[int], data: Any) -> None:
        self.shape = shape
        self.data = to_array(data) if isinstance(data, list) else data

    def is_scalar(self) -> bool:
        return self.shape == []

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, APLArray):
            return NotImplemented
        if self.shape != other.shape:
            return False
        if is_numeric_array(self.data) and is_numeric_array(other.data):
            return bool(np.array_equal(self.data, other.data))
        return to_list(self.data) == to_list(other.data)

    @classmethod
    def array(cls, shape: list[int], data: Any) -> 'APLArray':
        """Factory method for creating arrays."""
        return NumpyArray(shape, data)

    @classmethod
    def scalar(cls, value: Any) -> 'APLArray':
        """Factory method for creating scalars."""
        return NumpyArray([], [value])

    def __repr__(self) -> str:
        if self.is_scalar():
            return f"S({self.data[0]})"
        data_list = to_list(self.data) if is_numeric_array(self.data) else self.data
        return f"APLArray({self.shape}, {data_list})"

    # ── Monadic arithmetic ──

    @abstractmethod
    def conjugate(self) -> 'APLArray': ...
    @abstractmethod
    def signum(self) -> 'APLArray': ...
    @abstractmethod
    def negate(self) -> 'APLArray': ...
    @abstractmethod
    def reciprocal(self) -> 'APLArray': ...
    @abstractmethod
    def ceiling(self) -> 'APLArray': ...
    @abstractmethod
    def floor(self) -> 'APLArray': ...
    @abstractmethod
    def exponential(self) -> 'APLArray': ...
    @abstractmethod
    def natural_log(self) -> 'APLArray': ...
    @abstractmethod
    def absolute_value(self) -> 'APLArray': ...
    @abstractmethod
    def logical_not(self) -> 'APLArray': ...
    @abstractmethod
    def pi_times(self) -> 'APLArray': ...
    @abstractmethod
    def factorial(self) -> 'APLArray': ...

    # ── Monadic structural ──

    @abstractmethod
    def shape_of(self) -> 'APLArray': ...
    @abstractmethod
    def ravel(self) -> 'APLArray': ...
    @abstractmethod
    def reverse(self) -> 'APLArray': ...
    @abstractmethod
    def reverse_first(self) -> 'APLArray': ...
    @abstractmethod
    def transpose(self) -> 'APLArray': ...
    @abstractmethod
    def matrix_inverse(self) -> 'APLArray': ...

    # ── Monadic env-dependent ──

    @abstractmethod
    def iota(self, io: int = 1) -> 'APLArray': ...
    @abstractmethod
    def tally(self) -> 'APLArray': ...
    @abstractmethod
    def grade_up(self, io: int = 1) -> 'APLArray': ...
    @abstractmethod
    def grade_down(self, io: int = 1) -> 'APLArray': ...
    @abstractmethod
    def roll(self, io: int = 1) -> 'APLArray': ...
    @abstractmethod
    def format(self) -> 'APLArray': ...

    # ── Dyadic arithmetic ──

    @abstractmethod
    def add(self, other: 'APLArray') -> 'APLArray': ...
    @abstractmethod
    def subtract(self, other: 'APLArray') -> 'APLArray': ...
    @abstractmethod
    def multiply(self, other: 'APLArray') -> 'APLArray': ...
    @abstractmethod
    def divide(self, other: 'APLArray') -> 'APLArray': ...
    @abstractmethod
    def maximum(self, other: 'APLArray') -> 'APLArray': ...
    @abstractmethod
    def minimum(self, other: 'APLArray') -> 'APLArray': ...
    @abstractmethod
    def power(self, other: 'APLArray') -> 'APLArray': ...
    @abstractmethod
    def logarithm(self, other: 'APLArray') -> 'APLArray': ...
    @abstractmethod
    def residue(self, other: 'APLArray') -> 'APLArray': ...
    @abstractmethod
    def circular(self, other: 'APLArray') -> 'APLArray': ...
    @abstractmethod
    def binomial(self, other: 'APLArray') -> 'APLArray': ...

    # ── Dyadic comparisons ──

    @abstractmethod
    def less_than(self, other: 'APLArray', ct: float = 0) -> 'APLArray': ...
    @abstractmethod
    def less_equal(self, other: 'APLArray', ct: float = 0) -> 'APLArray': ...
    @abstractmethod
    def equal(self, other: 'APLArray', ct: float = 0) -> 'APLArray': ...
    @abstractmethod
    def greater_equal(self, other: 'APLArray', ct: float = 0) -> 'APLArray': ...
    @abstractmethod
    def greater_than(self, other: 'APLArray', ct: float = 0) -> 'APLArray': ...
    @abstractmethod
    def not_equal(self, other: 'APLArray', ct: float = 0) -> 'APLArray': ...

    # ── Dyadic logical / match / deal ──

    @abstractmethod
    def logical_and(self, other: 'APLArray') -> 'APLArray': ...
    @abstractmethod
    def logical_or(self, other: 'APLArray') -> 'APLArray': ...
    @abstractmethod
    def match(self, other: 'APLArray') -> 'APLArray': ...
    @abstractmethod
    def not_match(self, other: 'APLArray') -> 'APLArray': ...
    @abstractmethod
    def deal(self, other: 'APLArray', io: int = 1) -> 'APLArray': ...

    # ── Dyadic structural ──

    @abstractmethod
    def reshape(self, other: 'APLArray') -> 'APLArray': ...
    @abstractmethod
    def catenate(self, other: 'APLArray') -> 'APLArray': ...
    @abstractmethod
    def take(self, other: 'APLArray') -> 'APLArray': ...
    @abstractmethod
    def drop(self, other: 'APLArray') -> 'APLArray': ...
    @abstractmethod
    def rotate(self, other: 'APLArray') -> 'APLArray': ...
    @abstractmethod
    def rotate_first(self, other: 'APLArray') -> 'APLArray': ...
    @abstractmethod
    def encode(self, other: 'APLArray') -> 'APLArray': ...
    @abstractmethod
    def decode(self, other: 'APLArray') -> 'APLArray': ...
    @abstractmethod
    def replicate(self, other: 'APLArray') -> 'APLArray': ...
    @abstractmethod
    def replicate_first(self, other: 'APLArray') -> 'APLArray': ...
    @abstractmethod
    def expand(self, other: 'APLArray') -> 'APLArray': ...
    @abstractmethod
    def matrix_divide(self, other: 'APLArray') -> 'APLArray': ...
    @abstractmethod
    def index_of(self, other: 'APLArray', io: int = 1, ct: float = 0) -> 'APLArray': ...
    @abstractmethod
    def membership(self, other: 'APLArray', ct: float = 0) -> 'APLArray': ...
    @abstractmethod
    def from_array(self, other: 'APLArray', io: int = 1) -> 'APLArray': ...
    @abstractmethod
    def dyadic_format(self, other: 'APLArray') -> 'APLArray': ...


class NumpyArray(APLArray):
    """APLArray subclass backed by numpy arrays."""

    def _dyadic(self, other: 'APLArray',
                f: Any, bool_result: bool = False) -> 'APLArray':
        """Pervade a dyadic function element-wise with scalar extension."""
        from marple.errors import LengthError
        a_data = to_list(self.data)
        b_data = to_list(other.data)
        if self.is_scalar() and other.is_scalar():
            result = [f(a_data[0], b_data[0])]
            if bool_result:
                result = to_bool_array(result)
            return APLArray.array([], result)
        if self.is_scalar():
            data = [f(a_data[0], x) for x in b_data]
            if bool_result:
                data = to_bool_array(data)
            return APLArray.array(list(other.shape), data)
        if other.is_scalar():
            data = [f(x, b_data[0]) for x in a_data]
            if bool_result:
                data = to_bool_array(data)
            return APLArray.array(list(self.shape), data)
        if self.shape != other.shape:
            raise LengthError(f"Shape mismatch: {self.shape} vs {other.shape}")
        data = [f(a, b) for a, b in zip(a_data, b_data)]
        if bool_result:
            data = to_bool_array(data)
        return APLArray.array(list(self.shape), data)

    def _numeric_dyadic_op(self, other: 'APLArray', op: Any, upcast: bool = False) -> 'APLArray':
        """Apply a numeric operator (+, -, *, etc.) on numpy data."""
        from marple.errors import LengthError
        a = maybe_upcast(self.data) if upcast else self.data
        b = maybe_upcast(other.data) if upcast else other.data
        try:
            result = op(a, b)
        except ValueError:
            raise LengthError(f"Shape mismatch: {self.shape} vs {other.shape}")
        shape = list(other.shape) if not other.is_scalar() else list(self.shape)
        return APLArray.array(shape, result)

    def add(self, other: 'APLArray') -> 'APLArray':
        if is_numeric_array(self.data) and is_numeric_array(other.data):
            return self._numeric_dyadic_op(other, lambda a, b: a + b, upcast=True)
        return self._dyadic(other, lambda a, b: a + b)

    def subtract(self, other: 'APLArray') -> 'APLArray':
        if is_numeric_array(self.data) and is_numeric_array(other.data):
            return self._numeric_dyadic_op(other, lambda a, b: a - b, upcast=True)
        return self._dyadic(other, lambda a, b: a - b)

    def multiply(self, other: 'APLArray') -> 'APLArray':
        if is_numeric_array(self.data) and is_numeric_array(other.data):
            return self._numeric_dyadic_op(other, lambda a, b: a * b, upcast=True)
        return self._dyadic(other, lambda a, b: a * b)

    def divide(self, other: 'APLArray') -> 'APLArray':
        from marple.errors import DomainError
        if is_numeric_array(other.data):
            if np.any(other.data == 0):
                raise DomainError("Division by zero")
            return self._numeric_dyadic_op(other, lambda a, b: a / b)
        b_data = to_list(other.data)
        if any(x == 0 for x in b_data):
            raise DomainError("Division by zero")
        return self._dyadic(other, lambda a, b: a / b)

    def maximum(self, other: 'APLArray') -> 'APLArray':
        if is_numeric_array(self.data) and is_numeric_array(other.data):
            return self._numeric_dyadic_op(other, lambda a, b: np.maximum(a, b))
        return self._dyadic(other, lambda a, b: max(a, b))

    def minimum(self, other: 'APLArray') -> 'APLArray':
        if is_numeric_array(self.data) and is_numeric_array(other.data):
            return self._numeric_dyadic_op(other, lambda a, b: np.minimum(a, b))
        return self._dyadic(other, lambda a, b: min(a, b))

    def power(self, other: 'APLArray') -> 'APLArray':
        if is_numeric_array(self.data) and is_numeric_array(other.data):
            return self._numeric_dyadic_op(other, lambda a, b: a ** b, upcast=True)
        return self._dyadic(other, lambda a, b: a ** b)

    def logarithm(self, other: 'APLArray') -> 'APLArray':
        if is_numeric_array(self.data) and is_numeric_array(other.data):
            return self._numeric_dyadic_op(other, lambda a, b: np.log(b) / np.log(a))
        import math
        return self._dyadic(other, lambda a, b: math.log(b) / math.log(a))

    def residue(self, other: 'APLArray') -> 'APLArray':
        if is_numeric_array(self.data) and is_numeric_array(other.data):
            return self._numeric_dyadic_op(other, lambda a, b: b % a)
        return self._dyadic(other, lambda a, b: b % a)

    def circular(self, other: 'APLArray') -> 'APLArray':
        import math
        from marple.errors import DomainError
        _CIRCULAR: dict[int, Any] = {
            0: lambda x: math.sqrt(1 - x * x),
            1: math.sin, 2: math.cos, 3: math.tan,
            4: lambda x: math.sqrt(1 + x * x),
            5: math.sinh, 6: math.cosh, 7: math.tanh,
            -1: math.asin, -2: math.acos, -3: math.atan,
            -4: lambda x: math.sqrt(x * x - 1),
            -5: math.asinh, -6: math.acosh, -7: math.atanh,
        }
        def _apply(a: Any, b: Any) -> Any:
            fn = _CIRCULAR.get(int(a))
            if fn is None:
                raise DomainError(f"Unknown circular function selector: {a}")
            return fn(float(b))
        return self._dyadic(other, _apply)

    def binomial(self, other: 'APLArray') -> 'APLArray':
        import math
        def _binom(k: Any, n: Any) -> Any:
            return math.gamma(n + 1) / (math.gamma(k + 1) * math.gamma(n - k + 1))
        return self._dyadic(other, _binom)

    @staticmethod
    def _tolerant_eq(a: Any, b: Any, ct: float) -> Any:
        """Tolerant equality — works on scalars and numpy arrays."""
        if ct == 0:
            return a == b
        return abs(a - b) <= ct * np.maximum(abs(a), abs(b))

    def _compare(self, other: 'APLArray', op: Any, ct: float = 0) -> 'APLArray':
        """Comparison with numpy fast path and tolerant equality."""
        if is_numeric_array(self.data) and is_numeric_array(other.data):
            shape = list(other.shape) if not other.is_scalar() else list(self.shape)
            result = op(self.data, other.data, self._tolerant_eq(self.data, other.data, ct))
            return APLArray.array(shape, to_bool_array(result))
        return self._dyadic(other, lambda a, b: int(op(a, b, self._tolerant_eq(a, b, ct))), bool_result=True)

    def less_than(self, other: 'APLArray', ct: float = 0) -> 'APLArray':
        return self._compare(other, lambda a, b, eq: (a < b) & (1 - eq), ct)

    def less_equal(self, other: 'APLArray', ct: float = 0) -> 'APLArray':
        return self._compare(other, lambda a, b, eq: (a <= b) | eq, ct)

    def equal(self, other: 'APLArray', ct: float = 0) -> 'APLArray':
        return self._compare(other, lambda a, b, eq: eq, ct)

    def greater_equal(self, other: 'APLArray', ct: float = 0) -> 'APLArray':
        return self._compare(other, lambda a, b, eq: (a >= b) | eq, ct)

    def greater_than(self, other: 'APLArray', ct: float = 0) -> 'APLArray':
        return self._compare(other, lambda a, b, eq: (a > b) & (1 - eq), ct)

    def not_equal(self, other: 'APLArray', ct: float = 0) -> 'APLArray':
        return self._compare(other, lambda a, b, eq: 1 - eq, ct)

    def logical_and(self, other: 'APLArray') -> 'APLArray':
        if is_numeric_array(self.data) and is_numeric_array(other.data):
            shape = list(other.shape) if not other.is_scalar() else list(self.shape)
            return APLArray.array(shape, to_bool_array(self.data * other.data))
        return self._dyadic(other, lambda a, b: int(bool(a) and bool(b)), bool_result=True)

    def logical_or(self, other: 'APLArray') -> 'APLArray':
        if is_numeric_array(self.data) and is_numeric_array(other.data):
            shape = list(other.shape) if not other.is_scalar() else list(self.shape)
            result = self.data + other.data
            return APLArray.array(shape, to_bool_array(np.minimum(result, 1)))
        return self._dyadic(other, lambda a, b: int(bool(a) or bool(b)), bool_result=True)

    def match(self, other: 'APLArray') -> 'APLArray':
        return APLArray.scalar(1 if self == other else 0)

    def not_match(self, other: 'APLArray') -> 'APLArray':
        return APLArray.scalar(0 if self == other else 1)

    def deal(self, other: 'APLArray', io: int = 1) -> 'APLArray':
        """Dyadic ?: deal. N?M → N random integers from io..M without replacement."""
        import random as _random
        from marple.errors import LengthError
        n = int(self.data[0])
        m = int(other.data[0])
        if n > m:
            raise LengthError(f"Deal: cannot choose {n} from {m}")
        result = _random.sample(range(io, m + io), n)
        return APLArray.array([n], result)

    # ── Dyadic structural (delegate to structural.py) ──

    def reshape(self, other: 'APLArray') -> 'APLArray':
        from marple.structural import reshape
        return reshape(self, other)

    def catenate(self, other: 'APLArray') -> 'APLArray':
        from marple.structural import catenate
        return catenate(self, other)

    def take(self, other: 'APLArray') -> 'APLArray':
        from marple.structural import take
        return take(self, other)

    def drop(self, other: 'APLArray') -> 'APLArray':
        from marple.structural import drop
        return drop(self, other)

    def rotate(self, other: 'APLArray') -> 'APLArray':
        from marple.structural import rotate
        return rotate(self, other)

    def rotate_first(self, other: 'APLArray') -> 'APLArray':
        from marple.structural import rotate_first
        return rotate_first(self, other)

    def encode(self, other: 'APLArray') -> 'APLArray':
        from marple.structural import encode
        return encode(self, other)

    def decode(self, other: 'APLArray') -> 'APLArray':
        from marple.structural import decode
        return decode(self, other)

    def replicate(self, other: 'APLArray') -> 'APLArray':
        from marple.structural import replicate
        return replicate(self, other)

    def replicate_first(self, other: 'APLArray') -> 'APLArray':
        from marple.structural import replicate_first
        return replicate_first(self, other)

    def expand(self, other: 'APLArray') -> 'APLArray':
        from marple.structural import expand
        return expand(self, other)

    def matrix_divide(self, other: 'APLArray') -> 'APLArray':
        from marple.structural import matrix_divide
        return matrix_divide(self, other)

    def index_of(self, other: 'APLArray', io: int = 1, ct: float = 0) -> 'APLArray':
        from marple.structural import index_of
        return index_of(self, other, io, ct)

    def membership(self, other: 'APLArray', ct: float = 0) -> 'APLArray':
        from marple.structural import membership
        return membership(self, other, ct)

    def from_array(self, other: 'APLArray', io: int = 1) -> 'APLArray':
        from marple.structural import from_array
        return from_array(self, other, io)

    def dyadic_format(self, other: 'APLArray') -> 'APLArray':
        if self.is_scalar():
            width = int(self.data[0])
            precision = None
        else:
            width = int(self.data[0])
            precision = int(self.data[1]) if len(self.data) > 1 else None
        values = other.data if not other.is_scalar() else [other.data[0]]
        result_chars: list[str] = []
        for v in values:
            if precision is not None:
                formatted = f"{float(v):.{precision}f}"
            else:
                formatted = str(v)
            padded = " " * max(0, width - len(formatted)) + formatted
            result_chars.extend(list(padded))
        return APLArray.array([len(result_chars)], result_chars)

    def roll(self, io: int = 1) -> 'APLArray':
        """Monadic ?: roll. ?N → random int io..N, ?0 → random float [0,1)."""
        import random as _random
        def roll_one(v: object) -> object:
            n = int(v)  # type: ignore[arg-type]
            return _random.random() if n == 0 else _random.randint(io, n - 1 + io)
        if self.is_scalar():
            return APLArray.scalar(roll_one(self.data[0]))
        return APLArray.array(list(self.shape), [roll_one(v) for v in self.data])

    def format(self) -> 'APLArray':
        from marple.formatting import format_num
        if self.is_scalar():
            s = format_num(self.data[0])
        else:
            parts = [format_num(val) for val in self.data]
            s = " ".join(parts)
        return APLArray.array([len(s)], list(s))

    def grade_up(self, io: int = 1) -> 'APLArray':
        indexed = list(enumerate(self.data))
        indexed.sort(key=lambda pair: pair[1])  # type: ignore[arg-type]
        return APLArray.array([len(self.data)], [i + io for i, _ in indexed])

    def grade_down(self, io: int = 1) -> 'APLArray':
        indexed = list(enumerate(self.data))
        indexed.sort(key=lambda pair: pair[1], reverse=True)  # type: ignore[arg-type]
        return APLArray.array([len(self.data)], [i + io for i, _ in indexed])

    def iota(self, io: int = 1) -> 'APLArray':
        n = int(self.data[0])
        return APLArray.array([n], list(range(io, n + io)))

    def tally(self) -> 'APLArray':
        return APLArray.scalar(1) if self.is_scalar() else APLArray.scalar(self.shape[0])

    def conjugate(self) -> 'APLArray':
        """Monadic +: identity for real, conjugate for complex."""
        return APLArray.array(list(self.shape), list(self.data))

    def signum(self) -> 'APLArray':
        return APLArray.array(list(self.shape),
            [(-1 if x < 0 else 1 if x > 0 else 0) for x in to_list(self.data)])

    def negate(self) -> 'APLArray':
        if is_numeric_array(self.data):
            return APLArray.array(list(self.shape), -self.data)
        return APLArray.array(list(self.shape), [-x for x in to_list(self.data)])

    def reciprocal(self) -> 'APLArray':
        from marple.errors import DomainError
        data = to_list(self.data)
        if any(x == 0 for x in data):
            raise DomainError("Division by zero")
        if is_numeric_array(self.data):
            return APLArray.array(list(self.shape), 1.0 / self.data)
        return APLArray.array(list(self.shape), [1 / x for x in data])

    def ceiling(self) -> 'APLArray':
        if is_numeric_array(self.data):
            return APLArray.array(list(self.shape), np.ceil(self.data))
        import math
        return APLArray.array(list(self.shape), [math.ceil(x) for x in to_list(self.data)])

    def floor(self) -> 'APLArray':
        if is_numeric_array(self.data):
            return APLArray.array(list(self.shape), np.floor(self.data))
        import math
        return APLArray.array(list(self.shape), [math.floor(x) for x in to_list(self.data)])

    def exponential(self) -> 'APLArray':
        if is_numeric_array(self.data):
            return APLArray.array(list(self.shape), np.exp(self.data))
        import math
        return APLArray.array(list(self.shape), [math.exp(x) for x in to_list(self.data)])

    def natural_log(self) -> 'APLArray':
        if is_numeric_array(self.data):
            return APLArray.array(list(self.shape), np.log(self.data))
        import math
        return APLArray.array(list(self.shape), [math.log(x) for x in to_list(self.data)])

    def absolute_value(self) -> 'APLArray':
        if is_numeric_array(self.data):
            return APLArray.array(list(self.shape), abs(self.data))
        return APLArray.array(list(self.shape), [abs(x) for x in to_list(self.data)])

    def logical_not(self) -> 'APLArray':
        return APLArray.array(list(self.shape), to_bool_array([int(not x) for x in to_list(self.data)]))

    def pi_times(self) -> 'APLArray':
        import math
        if is_numeric_array(self.data):
            return APLArray.array(list(self.shape), self.data * math.pi)
        return APLArray.array(list(self.shape), [math.pi * x for x in to_list(self.data)])

    def factorial(self) -> 'APLArray':
        import math
        return APLArray.array(list(self.shape), [math.gamma(x + 1) for x in to_list(self.data)])

    def shape_of(self) -> 'APLArray':
        return APLArray.array([len(self.shape)], list(self.shape))

    def transpose(self) -> 'APLArray':
        from marple.errors import RankError
        if len(self.shape) <= 1:
            return APLArray.array(list(self.shape), list(self.data))
        if len(self.shape) != 2:
            raise RankError("Transpose currently supports only rank-2 arrays")
        rows, cols = self.shape
        new_data: list[object] = []
        for c in range(cols):
            for r in range(rows):
                new_data.append(self.data[r * cols + c])
        return APLArray.array([cols, rows], new_data)

    def matrix_inverse(self) -> 'APLArray':
        from marple.structural import matrix_inverse
        return matrix_inverse(self)

    def reverse(self) -> 'APLArray':
        if len(self.shape) <= 1:
            return APLArray.array(list(self.shape), list(reversed(self.data)))
        row_len = self.shape[-1]
        data = list(self.data)
        result: list[object] = []
        for r in range(len(data) // row_len):
            start = r * row_len
            result.extend(reversed(data[start:start + row_len]))
        return APLArray.array(list(self.shape), result)

    def reverse_first(self) -> 'APLArray':
        if len(self.shape) <= 1:
            return APLArray.array(list(self.shape), list(reversed(self.data)))
        chunk = 1
        for s in self.shape[1:]:
            chunk *= s
        n = self.shape[0]
        data = list(self.data)
        result: list[object] = []
        for r in range(n - 1, -1, -1):
            start = r * chunk
            result.extend(data[start:start + chunk])
        return APLArray.array(list(self.shape), result)

    def ravel(self) -> 'APLArray':
        return APLArray.array([len(self.data)], list(self.data))


def S(value: Any) -> APLArray:
    return APLArray.scalar(value)
