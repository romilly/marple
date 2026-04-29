from __future__ import annotations


from contextlib import contextmanager
from typing import Any, Callable, TYPE_CHECKING, Iterator, Self, cast

if TYPE_CHECKING:
    from marple.apl_value import PowerStrategy
    from marple.executor import Executor
    
from marple.errors import DomainError, LengthError, RankError
import numpy as np
from marple.apl_value import NC_ARRAY, APLValue
import numpy.typing as npt

NDArray = npt.NDArray[Any]
_CT = 1e-10  # comparison tolerance for GCD


DR_CODE_SPECS: "dict[str, int]" = {
    "uint8": 81,
    "int8": 83,
    "int16": 163,
    "uint32": 320,
    "int32": 323,
    "int64": 643,
    "float32": 325,
    "float64": 645,
}


def data_type_code(data: NDArray) -> int:
    """Return the ⎕DR type code for the given data.

    Encoding: first digits = bit width, last digit = type
    (0=char, 1=boolean, 3=signed int, 5=float, 7=decimal, 9=complex).
    """
    return DR_CODE_SPECS[data.dtype.name]

def _gcd_float(a: float, b: float) -> float:
    """GCD via Euclidean algorithm, tolerant of floating-point values."""
    a, b = abs(a), abs(b)
    while b > _CT:
        a, b = b, a % b
    return a

def is_numeric_array(data: NDArray) -> bool:
    """Check if data is a numeric ndarray from the active backend.

    Char-dtype arrays are reserved for character data (Unicode codepoints)
    and are NOT numeric — see is_char_array. The two predicates are
    disjoint, which is what allows the dyadic-arithmetic fast paths
    to use is_numeric_array as a safe gate after the char guards run.
    """
    return data.dtype != np.uint32

def is_int_dtype(arr: Any) -> bool:
    return bool(np.issubdtype(arr.dtype, np.integer))

def maybe_upcast(data: Any) -> Any:
    if not is_numeric_array(data) or not is_int_dtype(data):
        return data
    return data.astype(np.float64)

def is_float_dtype(arr: Any) -> bool:
        return bool(np.issubdtype(arr.dtype, np.floating))

def to_bool_array(data: "NDArray | list[int]") -> NDArray:
    """Convert data to a uint8 boolean array (0/1 values)."""
    return np.asarray(data, dtype=np.uint8)


def maybe_downcast(data: Any, ct: float) -> Any:
        if not is_float_dtype(data):
            return data
        if data.size == 0:
            return data
        rounded = np.round(data)
        diff = np.abs(data - rounded)
        if ct == 0:
            if not np.all(diff == 0):
                return data
        else:
            mag = np.maximum(np.abs(data), np.abs(rounded))
            if not np.all(diff <= ct * mag):
                return data
        max_val = np.max(np.abs(rounded))
        if max_val > np.float64(np.iinfo(np.int64).max):
            return data
        int_arr = rounded.astype(np.int64)
        if np.all(np.abs(int_arr) <= np.iinfo(np.int32).max):
            return int_arr.astype(np.int32)
        return int_arr

def numeric_upcast_dtype() -> Any:
    return np.float64

def np_gather(data: Any, axis_indices: "list[list[int]]") -> Any:
    """Multi-axis gather: return the flat sequence of
    `data[axis_indices[0][i0], axis_indices[1][i1], ...]` as (i0,i1,...)
    ranges over the Cartesian product of `axis_indices`.
    """
    idx_arrays = [np.asarray(ax) for ax in axis_indices]
    return data[np.ix_(*idx_arrays)].flatten()
 
def np_reshape(arr: Any, *shape: Any) -> Any:
    """ndarray.reshape.
    """
    if len(shape) == 1:
        s = shape[0]
        return arr.reshape(s)
    return arr.reshape(shape)

@contextmanager
def strict_numeric_errstate() -> Iterator[None]:
        with np.errstate(over="raise", invalid="raise"):
            yield

def str_to_char_array(s: str) -> NDArray:
    """Convert a Python string to a numpy array of codepoints."""
    return np.array([ord(c) for c in s], dtype=get_char_dtype())

@contextmanager
def ignoring_numeric_errstate() -> Iterator[None]:
    with np.errstate(over="ignore", invalid="ignore"):
        yield

def get_char_dtype() -> Any:
    """Return the currently active char dtype.
    """
    return np.uint32

class APLArray(APLValue):
    """APL array — the port. Concrete adapters live in numpy_aplarray.py
    (desktop, numpy) and ulab_aplarray.py (Pico, ulab).

    Interface methods below declare what each adapter must provide;
    their bodies raise NotImplementedError. Direct `APLArray(shape, data)`
    construction is supported — `__new__` dispatches to the active
    adapter — so tests stay backend-neutral.
    """

    # def __new__(cls, *args: Any, **kwargs: Any) -> Self:
    #     """Instantiating the port directly dispatches to the active adapter.

    #     Callers that write `APLArray(shape, data)` (common in tests that
    #     want to stay backend-neutral) get a `NumpyAPLArray` on CPython or
    #     a `UlabAPLArray` on MicroPython, whichever `backend_functions.
    #     get_backend_class()` returns at the time of the call.

    #     Calling a concrete subclass directly — `NumpyAPLArray(shape, data)`,
    #     `UlabAPLArray(shape, data)` — bypasses this dispatch and creates
    #     the named subclass as normal.
    #     """
    #     if cls is APLArray:
    #         # from marple.backend_functions import get_backend_class
    #         from marple.numpy_aplarray import NumpyAPLArray
    #         return cast(Self, object.__new__(NumpyAPLArray))
    #     return object.__new__(cls)

    # ---- backend hooks (declared on the port; adapters implement) -----

    @classmethod
    def char_dtype(cls) -> Any:
        return np.uint32
    
    @classmethod
    @contextmanager
    def strict_numeric_errstate(cls) -> Iterator[None]:
        with np.errstate(over="raise", invalid="raise"):
            yield

    @classmethod
    def ignoring_numeric_errstate(cls) -> Any:
        """Context manager wrapping numeric ops that suppress overflow
        warnings. Same shape as `strict_numeric_errstate`, but configured
        to ignore rather than raise.
        """
        raise NotImplementedError(
            "adapter must implement ignoring_numeric_errstate")

    @classmethod
    def is_int_dtype(cls, arr: Any) -> bool:
        """True iff `arr.dtype` is one of the backend's integer dtypes."""
        raise NotImplementedError("adapter must implement is_int_dtype")

    @classmethod
    def is_float_dtype(cls, arr: Any) -> bool:
        """True iff `arr.dtype` is one of the backend's float dtypes."""
        raise NotImplementedError("adapter must implement is_float_dtype")


    @classmethod
    def maybe_upcast(cls, data: Any) -> Any:
        """Upcast integer arrays to the backend's widest float before
        overflow-prone arithmetic. Numeric-only (char arrays pass through).
        """
        raise NotImplementedError("adapter must implement maybe_upcast")

    @classmethod
    def numeric_upcast_dtype(cls) -> Any:
        """Widest float dtype the backend supports — used as the `dtype`
        kwarg for zeros/full arrays in reduce/scan accumulators.
        """
        raise NotImplementedError(
            "adapter must implement numeric_upcast_dtype")

    @classmethod
    def reshape_ndarray(cls, arr: Any, shape: Any) -> Any:
        """Reshape `arr` to `shape`. Adapter normalises arg form as its
        backend requires.
        """
        raise NotImplementedError("adapter must implement reshape_ndarray")

    @classmethod
    def repeat_ndarray(cls, arr: Any, counts: Any, axis: int) -> Any:
        """Repeat elements of `arr` along `axis` according to `counts`
        (an int or a per-element sequence). Matches np.repeat's calling
        convention.
        """
        raise NotImplementedError("adapter must implement repeat_ndarray")

    @classmethod
    def gather_ndarray(cls, data: Any, axis_indices: "list[list[int]]") -> Any:
        """Multi-axis Cartesian-product gather. Flat ndarray of
        `data[i0, i1, …]` over every combination in the axis_indices.
        Caller reshapes to the desired rank.
        """
        raise NotImplementedError("adapter must implement gather_ndarray")

    @classmethod
    def maybe_downcast(cls, data: Any, ct: float) -> Any:
        """Convert float arrays to int if all elements are close to whole
        numbers within APL tolerance `ct`. Adapters choose their widest
        signed int target.
        """
        raise NotImplementedError("adapter must implement maybe_downcast")

    # ---- array-level port methods (declared here; adapters implement) ----

    def as_str(self) -> str:
        return ''.join(chr(int(x)) for x in self.data.flat)

    def is_char(self) -> bool:
        return self.data.dtype == self.char_dtype()

    def is_numeric(self) -> bool:
        return self.data.dtype != self.char_dtype()

    def to_list(self) -> list[Any]:
        if len(self.data.shape) == 0:
            return [self.data.item()]
        return self.data.tolist()

    def dtype_code(self) -> int:
        """Return this array's ⎕DR numeric type code.

        Encoding: leading digits = bit width; trailing digit = class
        (0 = char, 3 = signed int, 5 = float). Used by the ⎕DR
        system function.
        """
        raise NotImplementedError("adapter must implement dtype_code")

    def slice_axis(self, axis: int, index: int) -> APLArray:
        rank = len(self.shape)
        if axis < 0 or axis >= rank:
            raise ValueError(
                "axis {} out of range for rank-{} array".format(axis, rank))
        idx = tuple(index if i == axis else slice(None) for i in range(rank))
        sliced = self.data[idx]
        new_shape = [s for i, s in enumerate(self.shape) if i != axis]
        return type(self)(new_shape, sliced)

    def __init__(self, shape: list[int], data: list[Any] | np.ndarray[Any, Any]) -> None:
        self.shape = shape
        self.data = np.asarray(data)
        if self.data.shape != shape:
            self.data = self.data.reshape(shape)

    def is_scalar(self) -> bool:
        return self.shape == []
    

    def scalar_value(self) -> Any:
        """Return the native Python value for scalar storage.

        Platform-agnostic replacement for bare `self.data.item()` calls —
        desktop numpy 0-d arrays have `.item()`; ulab 1-d length-1 arrays
        don't and have to be unwrapped via `data[0]`. `scalar_item` in
        backend_functions handles both; this method is just sugar so call
        sites don't need to see the shim.
        """
        return self.data.item()


    def name_class(self) -> int:
        return NC_ARRAY

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, APLArray):
            return NotImplemented
        if self.shape != other.shape:
            return False
        # Mixed char/numeric arrays are never equal, even if the
        # numeric values happen to match the character codepoints.
        if self.is_char() != other.is_char():
            return False
        return bool(np.array_equal(self.data, other.data))

    @classmethod
    def array(cls, shape: list[int], data: Any) -> APLArray:
        """Factory method for creating arrays.

        On the port itself (`APLArray.array(...)`) dispatches to the
        active adapter. On a concrete subclass constructs that subclass.
        """
        return cls(shape, data)

    @classmethod
    def scalar(cls, value: Any) -> APLArray:
        """Factory method for creating scalars.

        APL shape is `[]`. Underlying storage is 0-d on desktop numpy
        and 1-d length-1 on ulab — see __init__ for the invariant.
        On the port itself (`APLArray.scalar(...)`) dispatches to the
        active adapter.
        """
        if isinstance(value, str):
            return cls([], str_to_char_array(value))
        return cls([], value)

    def __repr__(self) -> str:
        if self.is_scalar():
            return f"S({self.scalar_value()})"
        return f"APLArray({self.shape}, {self.to_list()})"

    def _dyadic(self, other: APLArray,
                f: Callable[[Any, Any], Any], bool_result: bool = False) -> APLArray:
        """Pervade a dyadic function element-wise with scalar extension."""
        a_data = self.to_list()
        b_data = other.to_list()
        cls = type(self)
        if self.is_scalar() and other.is_scalar():
            result = [f(a_data[0], b_data[0])]
            if bool_result:
                result = to_bool_array(result)
            return cls.array([], result)
        if self.is_scalar():
            data = [f(a_data[0], x) for x in b_data]
            if bool_result:
                data = to_bool_array(data)
            return cls.array(list(other.shape), data)
        if other.is_scalar():
            data = [f(x, b_data[0]) for x in a_data]
            if bool_result:
                data = to_bool_array(data)
            return cls.array(list(self.shape), data)
        if self.shape != other.shape:
            raise LengthError(f"Shape mismatch: {self.shape} vs {other.shape}")
        data = [f(a, b) for a, b in zip(a_data, b_data)]
        if bool_result:
            data = to_bool_array(data)
        return cls.array(list(self.shape), data)

    def _numeric_dyadic_op(self, other: APLArray, op: Callable[[Any, Any], Any], upcast: bool = False) -> APLArray:
        """Apply a numeric operator (+, -, *, etc.) on numpy data.

        Backend override hook. All dyadic numeric arithmetic in APLArray
        funnels through this method. A subclass (e.g. UlabAPLArray) may
        override it to swap the numpy-specific machinery: `np.errstate`
        overflow trapping, `maybe_upcast` int→float promotion, and the
        `FloatingPointError`-to-`DomainError` translation.

        `maybe_upcast` promotes integer arrays to float64 before the
        op, which prevents integer-overflow silent-wrap at the cost of
        precision for very large ints. If the float operation then
        overflows to ±inf, that's a genuine arithmetic limit — raise
        DomainError rather than propagating ∞ silently.
        """
        a = maybe_upcast(self.data) if upcast else self.data
        b = maybe_upcast(other.data) if upcast else other.data
        try:
            with strict_numeric_errstate():
                result = op(a, b)
        except FloatingPointError:
            raise DomainError("arithmetic overflow")
        except ValueError:
            raise LengthError(f"Shape mismatch: {self.shape} vs {other.shape}")
        if not isinstance(result, np.ndarray):
            result = np.asarray(result)
        shape = list(other.shape) if not other.is_scalar() else list(self.shape)
        return type(self).array(shape, result)

    def _reject_chars(self, other: APLArray, op_name: str) -> None:
        """Raise DomainError if either operand is a character array.

        Must be called before any is_numeric_array fast path so that the
        future uint32 character representation is also caught.
        """
        if self.is_char() or other.is_char():
            raise DomainError(f"{op_name} is not defined on character data")

    def _reject_chars_monadic(self, op_name: str) -> None:
        """Raise DomainError if self is a character array (monadic ops)."""
        if self.is_char():
            raise DomainError(f"{op_name} is not defined on character data")

    def add(self, other: APLArray) -> APLArray:
        self._reject_chars(other, "+")
        if self.is_numeric() and other.is_numeric():
            return self._numeric_dyadic_op(other, lambda a, b: a + b, upcast=True)
        return self._dyadic(other, lambda a, b: a + b)

    def subtract(self, other: APLArray) -> APLArray:
        self._reject_chars(other, "-")
        if self.is_numeric() and other.is_numeric():
            return self._numeric_dyadic_op(other, lambda a, b: a - b, upcast=True)
        return self._dyadic(other, lambda a, b: a - b)

    def multiply(self, other: APLArray) -> APLArray:
        self._reject_chars(other, "×")
        if self.is_numeric() and other.is_numeric():
            return self._numeric_dyadic_op(other, lambda a, b: a * b, upcast=True)
        return self._dyadic(other, lambda a, b: a * b)

    def divide(self, other: APLArray) -> APLArray:
        self._reject_chars(other, "÷")
        if other.is_numeric():
            if np.any(other.data == 0):
                raise DomainError("Division by zero")
            return self._numeric_dyadic_op(other, lambda a, b: a / b)
        b_data = other.to_list()
        if any(x == 0 for x in b_data):
            raise DomainError("Division by zero")
        return self._dyadic(other, lambda a, b: a / b)

    def maximum(self, other: APLArray) -> APLArray:
        self._reject_chars(other, "⌈")
        if self.is_numeric() and other.is_numeric():
            return self._numeric_dyadic_op(other, lambda a, b: np.maximum(a, b))
        return self._dyadic(other, lambda a, b: max(a, b))

    def minimum(self, other: APLArray) -> APLArray:
        self._reject_chars(other, "⌊")
        if self.is_numeric() and other.is_numeric():
            return self._numeric_dyadic_op(other, lambda a, b: np.minimum(a, b))
        return self._dyadic(other, lambda a, b: min(a, b))

    def power(self, other: APLArray) -> APLArray:
        self._reject_chars(other, "*")
        if self.is_numeric() and other.is_numeric():
            return self._numeric_dyadic_op(other, lambda a, b: a ** b, upcast=True)
        return self._dyadic(other, lambda a, b: a ** b)

    def logarithm(self, other: APLArray) -> APLArray:
        self._reject_chars(other, "⍟")
        if self.is_numeric() and other.is_numeric():
            return self._numeric_dyadic_op(other, lambda a, b: np.log(b) / np.log(a))
        import math
        return self._dyadic(other, lambda a, b: math.log(b) / math.log(a))

    def residue(self, other: APLArray) -> APLArray:
        self._reject_chars(other, "|")
        if self.is_numeric() and other.is_numeric():
            return self._numeric_dyadic_op(other, lambda a, b: b % a)
        return self._dyadic(other, lambda a, b: b % a)

    def circular(self, other: APLArray) -> APLArray:
        self._reject_chars(other, "○")
        import math
        _CIRCULAR: dict[int, Callable[[float], float]] = {
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

    def binomial(self, other: APLArray) -> APLArray:
        self._reject_chars(other, "!")
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

    def _compare(self, other: APLArray, op: Callable[[Any, Any, Any], Any], ct: float = 0) -> APLArray:
        """Comparison with numpy fast path and tolerant equality."""
        if not self.is_numeric() or not other.is_numeric():
            ct = 0
        if self.is_numeric() and other.is_numeric():
            shape = list(other.shape) if not other.is_scalar() else list(self.shape)
            result = op(self.data, other.data, self._tolerant_eq(self.data, other.data, ct))
            return type(self).array(shape, to_bool_array(result))
        return self._dyadic(other, lambda a, b: int(op(a, b, self._tolerant_eq(a, b, ct))), bool_result=True)

    def less_than(self, other: APLArray, ct: float = 0) -> APLArray:
        return self._compare(other, lambda a, b, eq: (a < b) & (1 - eq), ct)

    def less_equal(self, other: APLArray, ct: float = 0) -> APLArray:
        return self._compare(other, lambda a, b, eq: (a <= b) | eq, ct)

    def equal(self, other: APLArray, ct: float = 0) -> APLArray:
        return self._compare(other, lambda a, b, eq: eq, ct)

    def greater_equal(self, other: APLArray, ct: float = 0) -> APLArray:
        return self._compare(other, lambda a, b, eq: (a >= b) | eq, ct)

    def greater_than(self, other: APLArray, ct: float = 0) -> APLArray:
        return self._compare(other, lambda a, b, eq: (a > b) & (1 - eq), ct)

    def not_equal(self, other: APLArray, ct: float = 0) -> APLArray:
        return self._compare(other, lambda a, b, eq: 1 - eq, ct)

    def logical_and(self, other: APLArray) -> APLArray:
        """∧ — LCM (least common multiple). Matches AND for boolean inputs."""
        self._reject_chars(other, "∧")
        if is_int_dtype(self.data) and is_int_dtype(other.data):
            g = np.gcd(self.data.astype(np.int64), other.data.astype(np.int64))
            result = np.where(g == 0, 0, np.abs(self.data * other.data) // g)
            shape = list(other.shape) if not other.is_scalar() else list(self.shape)
            return type(self).array(shape, result)
        return self._dyadic(other, lambda a, b: abs(a * b) / _gcd_float(a, b) if a and b else 0)

    def logical_or(self, other: APLArray) -> APLArray:
        """∨ — GCD (greatest common divisor). Matches OR for boolean inputs."""
        self._reject_chars(other, "∨")
        if is_int_dtype(self.data) and is_int_dtype(other.data):
            result = np.gcd(self.data.astype(np.int64), other.data.astype(np.int64))
            shape = list(other.shape) if not other.is_scalar() else list(self.shape)
            return type(self).array(shape, result)
        return self._dyadic(other, lambda a, b: _gcd_float(a, b))

    def match(self, other: APLArray) -> APLArray:
        return type(self).scalar(1 if self == other else 0)

    def not_match(self, other: APLArray) -> APLArray:
        return type(self).scalar(0 if self == other else 1)

    def deal(self, other: APLArray, io: int = 1) -> APLArray:
        """Dyadic ?: deal. N?M -> N random integers from io..M without replacement."""
        import random as _random
        n = int(self.scalar_value())
        m = int(other.scalar_value())
        if n > m:
            raise LengthError(f"Deal: cannot choose {n} from {m}")
        result = _random.sample(range(io, m + io), n)
        return type(self).array([n], result)

    # -- Dyadic structural (delegate to structural.py) --

    def reshape(self, other: APLArray) -> APLArray:
        """Dyadic ⍴: reshape `other` into the shape given by `self`.
        Values are cycled if the new shape is larger than `other`'s size;
        truncated if smaller. Empty `other` is filled with 0 (numeric)
        or the space codepoint (char).
        """
        raise NotImplementedError("adapter must implement reshape")

    def catenate(self, other: APLArray) -> APLArray:
        """Dyadic ,: catenate `self` with `other` along the last axis.

        Scalar + scalar → rank-1 2-element vector. Rank ≤ 1 cases
        produce a 1-D concatenation. Higher ranks: lower-rank operand
        is promoted with leading length-1 axes, then concatenated.
        """
        raise NotImplementedError("adapter must implement catenate")

    @classmethod
    def _build_like(cls, data: list[Any], shape: list[int],
                    source: "APLArray") -> "APLArray":
        """Construct an array with the same dtype as `source`. Used by
        take/drop/expand to keep result dtypes consistent with input
        (empty or reshaped results preserve char vs numeric typing).
        """
        raise NotImplementedError("adapter must implement _build_like")

    def take(self, other: APLArray) -> APLArray:
        """Dyadic ↑: take elements of `other` along each axis, per counts
        in `self`. Negative counts take from the end. Overtake pads with
        fill element (0 for numeric, space for char)."""
        raise NotImplementedError("adapter must implement take")

    def drop(self, other: APLArray) -> APLArray:
        """Dyadic ↓: drop elements of `other` along each axis, per counts
        in `self`. Negative counts drop from the end."""
        raise NotImplementedError("adapter must implement drop")

    def rotate(self, other: APLArray) -> APLArray:
        """Dyadic ⌽: rotate `other` along its last axis by `self` (a scalar
        or 1-element count)."""
        raise NotImplementedError("adapter must implement rotate")

    def rotate_first(self, other: APLArray) -> APLArray:
        """Dyadic ⊖: rotate `other` along its first axis by `self`."""
        raise NotImplementedError("adapter must implement rotate_first")

    def encode(self, other: APLArray) -> APLArray:
        """Dyadic ⊤: represent `other` in the number system given by `self`."""
        raise NotImplementedError("adapter must implement encode")

    def decode(self, other: APLArray) -> APLArray:
        """Dyadic ⊥: evaluate `other` as a polynomial with bases from `self`."""
        raise NotImplementedError("adapter must implement decode")

    def replicate(self, other: APLArray) -> APLArray:
        """Dyadic /: replicate/compress `other` along its last axis, using
        `self` as counts. Scalar self extends to match the axis length."""
        raise NotImplementedError("adapter must implement replicate")

    def replicate_first(self, other: APLArray) -> APLArray:
        """Dyadic ⌿: replicate/compress `other` along its first axis."""
        raise NotImplementedError("adapter must implement replicate_first")

    def expand(self, other: APLArray) -> APLArray:
        """Dyadic \\: expand `other` along its last axis using `self` as
        the 0/1 mask. Each 1 consumes the next element of `other`; each
        0 inserts a fill element."""
        raise NotImplementedError("adapter must implement expand")

    def matrix_divide(self, other: APLArray) -> APLArray:
        """Dyadic ⌹: solve `other x = self` for x. ulab adapters raise
        NotImplementedError (no np.linalg).
        """
        raise NotImplementedError("adapter must implement matrix_divide")

    @staticmethod
    def _tolerant_match(a: object, b: object, ct: float) -> bool:
        """Compare two values with APL tolerance for floats."""
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            if ct == 0:
                return a == b
            return abs(float(a) - float(b)) <= ct * max(abs(float(a)), abs(float(b)))
        return a == b

    def index_of(self, other: APLArray, io: int = 1, ct: float = 0) -> APLArray:
        """Dyadic ⍳: first position in `self` where each element of `other`
        is found (tolerant comparison), or len(self)+io if not found.
        """
        data = self.to_list()
        if other.is_scalar():
            target = other.scalar_value()
            for i, val in enumerate(data):
                if APLArray._tolerant_match(val, target, ct):
                    return S(i + io)
            return S(len(data) + io)
        targets = other.to_list()
        results: list[object] = []
        for target in targets:
            found = False
            for i, val in enumerate(data):
                if APLArray._tolerant_match(val, target, ct):
                    results.append(i + io)
                    found = True
                    break
            if not found:
                results.append(len(data) + io)
        return type(self).array(list(other.shape), results)

    def membership(self, other: APLArray, ct: float = 0) -> APLArray:
        """Dyadic ∈: for each element of `self`, 1 if found in `other`, else 0."""
        right_data = other.to_list()
        if self.is_scalar():
            val = self.scalar_value()
            for r in right_data:
                if APLArray._tolerant_match(val, r, ct):
                    return S(1)
            return S(0)
        left_data = self.to_list()
        results: list[object] = []
        for val in left_data:
            found = 0
            for r in right_data:
                if APLArray._tolerant_match(val, r, ct):
                    found = 1
                    break
            results.append(found)
        return type(self).array(list(self.shape), results)

    def from_array(self, other: APLArray, io: int = 1) -> APLArray:
        """Dyadic ⌷: select major cells of `other` at indices in `self`."""
        raise NotImplementedError("adapter must implement from_array")

    def transpose_dyadic(self, other: APLArray, io: int = 1) -> APLArray:
        """Dyadic ⍉: transpose `other` by axis permutation `self`. Supports
        diagonal extraction via repeated indices. Uses np.indices + fancy
        indexing — ulab adapters raise NotImplementedError.
        """
        raise NotImplementedError("adapter must implement transpose_dyadic")

    def dyadic_format(self, other: APLArray) -> APLArray:
        # Spec is a scalar (width only) or a 2-element vector
        # (width, precision). Use .item() / flat for the extraction so
        # this works with both 0-d and 1-d (1,) scalar storage.
        spec_flat = np.atleast_1d(self.data)
        width = int(spec_flat[0])
        precision = int(spec_flat[1]) if len(spec_flat) > 1 else None
        fmt = f"%.{precision}f" if precision is not None else "%s"
        # Format every element, then reshape.
        # Result shape: leading dims unchanged, last dim becomes last_dim * width.
        values = np.atleast_1d(other.data)
        strs = np.char.mod(fmt, values.ravel())
        strs = np.char.rjust(strs, width)
        # Join groups of last-axis elements into row strings
        last_dim = other.shape[-1] if other.shape else 1
        flat_texts = ["".join(strs[i:i + last_dim].tolist())
                       for i in range(0, len(strs), last_dim)]
        all_chars = np.concatenate(
            [str_to_char_array(t) for t in flat_texts]
        )
        if other.shape:
            result_shape = list(other.shape)
            result_shape[-1] = last_dim * width
        else:
            result_shape = [width]
        return type(self)(result_shape, all_chars)

    def roll(self, io: int = 1) -> APLArray:
        """Monadic ?: roll. ?N -> random int io..N, ?0 -> random float [0,1)."""
        import random as _random
        def roll_one(v: object) -> object:
            n = int(v)  # type: ignore[arg-type]
            return _random.random() if n == 0 else _random.randint(io, n - 1 + io)
        if self.is_scalar():
            return type(self).scalar(roll_one(self.scalar_value()))
        data = np.array([roll_one(v) for v in self.data.flat])
        return type(self)(list(self.shape), data.reshape(self.shape) if self.shape else data)

    def format(self) -> APLArray:
        from marple.formatting import format_num
        if self.is_scalar():
            s = format_num(self.scalar_value())
        else:
            parts = [format_num(val) for val in self.data]
            s = " ".join(parts)
        return type(self)([len(s)], str_to_char_array(s))

    def grade_up(self, io: int = 1) -> APLArray:
        if len(self.shape) != 1:
            raise RankError("⍋ requires a vector argument")
        vals = self.to_list()
        indexed = sorted(enumerate(vals), key=lambda pair: pair[1])  # type: ignore[arg-type,return-value]
        return type(self).array([len(vals)], [i + io for i, _ in indexed])

    def grade_down(self, io: int = 1) -> APLArray:
        if len(self.shape) != 1:
            raise RankError("⍒ requires a vector argument")
        vals = self.to_list()
        indexed = sorted(enumerate(vals), key=lambda pair: pair[1], reverse=True)  # type: ignore[arg-type,return-value]
        return type(self).array([len(vals)], [i + io for i, _ in indexed])

    def iota(self, io: int = 1) -> APLArray:
        n = int(self.scalar_value())
        return type(self).array([n], list(range(io, n + io)))

    def tally(self) -> APLArray:
        # Monadic ≢: number of major cells of Y. Per ISO/Dyalog,
        # this is the length of the leading axis, or 1 for a scalar.
        # NB: NOT the total element count (×/⍴Y) — the previous TODO
        # comment here was misleading and is now removed.
        return type(self).scalar(1) if self.is_scalar() else type(self).scalar(self.shape[0])

    def conjugate(self) -> APLArray:
        """Monadic +: identity for real, conjugate for complex."""
        self._reject_chars_monadic("monadic +")
        return type(self).array(list(self.shape), np.conjugate(self.data))

    def signum(self) -> APLArray:
        self._reject_chars_monadic("monadic ×")
        return type(self).array(list(self.shape),
            [(-1 if x < 0 else 1 if x > 0 else 0) for x in self.to_list()])

    def negate(self) -> APLArray:
        self._reject_chars_monadic("monadic -")
        return self._primitive_negate()

    def _primitive_negate(self) -> APLArray:
        """Backend override hook for monadic −.

        A subclass (e.g. UlabAPLArray) may override to use a different numeric
        backend for the numeric fast path. The list fallback is backend-agnostic.
        """
        cls = type(self)
        if self.is_numeric():
            return cls.array(list(self.shape), -self.data)
        return cls.array(list(self.shape), [-x for x in self.to_list()])

    def reciprocal(self) -> APLArray:
        self._reject_chars_monadic("monadic ÷")
        return self._primitive_reciprocal()

    def _primitive_reciprocal(self) -> APLArray:
        """Backend override hook for monadic ÷.

        Must raise `DomainError("Division by zero")` if any element is zero.
        A subclass may override to use a different numeric backend for the
        numeric fast path. The list fallback is backend-agnostic.
        """
        cls = type(self)
        if self.is_numeric():
            if np.any(self.data == 0):
                raise DomainError("Division by zero")
            return cls.array(list(self.shape), 1.0 / self.data)
        data = self.to_list()
        if any(x == 0 for x in data):
            raise DomainError("Division by zero")
        return cls.array(list(self.shape), [1 / x for x in data])

    def ceiling(self) -> APLArray:
        self._reject_chars_monadic("monadic ⌈")
        return type(self).array(list(self.shape), np.ceil(self.data))

    def floor(self) -> APLArray:
        self._reject_chars_monadic("monadic ⌊")
        return type(self).array(list(self.shape), np.floor(self.data))

    def exponential(self) -> APLArray:
        self._reject_chars_monadic("monadic *")
        return type(self).array(list(self.shape), np.exp(self.data))

    def natural_log(self) -> APLArray:
        self._reject_chars_monadic("monadic ⍟")
        return type(self).array(list(self.shape), np.log(self.data))

    def absolute_value(self) -> APLArray:
        self._reject_chars_monadic("monadic |")
        return type(self).array(list(self.shape), abs(self.data))

    def logical_not(self) -> APLArray:
        if self.is_numeric():
            return type(self).array(list(self.shape), to_bool_array(1 - self.data))
        return type(self).array(list(self.shape), to_bool_array([int(not x) for x in self.to_list()]))

    def pi_times(self) -> APLArray:
        self._reject_chars_monadic("monadic ○")
        import math
        return type(self).array(list(self.shape), self.data * math.pi)

    def factorial(self) -> APLArray:
        self._reject_chars_monadic("monadic !")
        import math
        return type(self).array(list(self.shape), [math.gamma(x + 1) for x in self.to_list()])

    def shape_of(self) -> APLArray:
        return type(self).array([len(self.shape)], list(self.shape))

    def transpose(self) -> APLArray:
        # Monadic ⍉: reverse the order of axes. Per the spec,
        # ⍴⍉Y = ⌽⍴Y. For rank ≤ 1 this is identity; otherwise use
        # np.transpose when available (numpy) or `.T` as a fallback
        # (ulab — its ndarray.T does the full-reverse transpose that
        # monadic ⍉ specifies).
        if len(self.shape) <= 1:
            return type(self)(list(self.shape), self.data.copy())
        transposed = np.transpose(self.data) if hasattr(np, "transpose") else self.data.T
        return type(self)(list(reversed(self.shape)), transposed.copy())

    def matrix_inverse(self) -> APLArray:
        """Monadic ⌹: matrix inverse. Requires a square matrix. ulab
        adapters raise NotImplementedError (no np.linalg).
        """
        raise NotImplementedError("adapter must implement matrix_inverse")

    def reverse(self) -> APLArray:
        # Scalar reverse is identity; np.flip needs at least one axis.
        if self.shape == []:
            return type(self)([], self.data.copy())
        return type(self)(list(self.shape), np.flip(self.data, axis=-1).copy())

    def reverse_first(self) -> APLArray:
        if self.shape == []:
            return type(self)([], self.data.copy())
        return type(self)(list(self.shape), np.flip(self.data, axis=0).copy())

    def ravel(self) -> APLArray:
        flat = self.data.flatten()
        return type(self)([len(flat)], flat)

    def as_power_strategy(self, ctx: 'Executor') -> 'PowerStrategy':
        from marple.apl_value import PowerByCount
        if not self.is_scalar():
            from marple.errors import DomainError
            raise DomainError("⍣ right operand must be scalar integer or function")
        return PowerByCount(int(self.scalar_value()))

_DOWNCAST_CT: float = 1e-14

def S(value: Any) -> APLArray:
    # Construct whichever APLArray subclass is active — NumpyAPLArray by
    # default on desktop, UlabAPLArray on the Pico. Route through the
    # backend_functions registry so subclass method overrides (e.g.
    # UlabAPLArray._numeric_dyadic_op) fire on the resulting instance.
    # Lazy import avoids an import cycle with backend_functions.
    from marple.numpy_aplarray import NumpyAPLArray
    return NumpyAPLArray.scalar(value)

