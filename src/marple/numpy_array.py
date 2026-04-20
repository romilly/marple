from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Callable, Iterator, TYPE_CHECKING

if TYPE_CHECKING:
    from marple.apl_value import PowerStrategy
    from marple.executor import Executor

from marple.backend_functions import (
    SCALAR_STORAGE_SHAPE,
    is_char_array, is_int_dtype, is_numeric_array, maybe_upcast,
    scalar_item, str_to_char_array, strict_numeric_errstate,
    to_array, to_bool_array, to_list,
)
from marple.errors import DomainError, LengthError, RankError
from marple.get_numpy import np
from marple.apl_value import NC_ARRAY, APLValue

_CT = 1e-10  # comparison tolerance for GCD


def _gcd_float(a: float, b: float) -> float:
    """GCD via Euclidean algorithm, tolerant of floating-point values."""
    a, b = abs(a), abs(b)
    while b > _CT:
        a, b = b, a % b
    return a


class APLArray(APLValue):
    """APL array backed by numpy arrays."""

    @classmethod
    def char_dtype(cls) -> Any:
        """Dtype used for character data (Unicode codepoints).

        Returned as a bare dtype token — `np.uint32` on numpy, an int-like
        constant on ulab (which has no `np.dtype` factory). Compare with
        `arr.dtype == char_dtype()`; use as the `dtype=` kwarg to
        `np.array(...)` — both forms work on numpy and ulab.

        Backend override hook: a subclass returns a narrower dtype when the
        underlying array library cannot support uint32 (e.g. ulab caps at
        uint16). BMP-only codepoints fit in uint16; APL glyphs are in the BMP.
        """
        return np.uint32

    @classmethod
    @contextmanager
    def strict_numeric_errstate(cls) -> Iterator[None]:
        """Context manager wrapping numeric ops that must trap overflow.

        Backend override hook. NumpyAPLArray uses `np.errstate(over="raise",
        invalid="raise")` so callers can catch `FloatingPointError` and
        convert to `DomainError`. A ulab-backed subclass yields a no-op —
        ulab has no errstate equivalent, so silent overflow is accepted.
        """
        with np.errstate(over="raise", invalid="raise"):
            yield

    @classmethod
    @contextmanager
    def ignoring_numeric_errstate(cls) -> Iterator[None]:
        """Context manager wrapping numeric ops that suppress overflow warnings.

        Backend override hook. NumpyAPLArray uses `np.errstate(over="ignore",
        invalid="ignore")` so callers can inspect inf/nan without printing
        numpy RuntimeWarnings. A ulab-backed subclass yields a no-op.
        """
        with np.errstate(over="ignore", invalid="ignore"):
            yield

    @classmethod
    def is_int_dtype(cls, arr: Any) -> bool:
        """Backend override hook. Numpy uses `np.issubdtype(…, np.integer)`;
        ulab has no issubdtype, so its subclass checks against a known set.
        """
        return bool(np.issubdtype(arr.dtype, np.integer))

    @classmethod
    def is_float_dtype(cls, arr: Any) -> bool:
        """Backend override hook. See `is_int_dtype`."""
        return bool(np.issubdtype(arr.dtype, np.floating))

    @classmethod
    def maybe_upcast(cls, data: Any) -> Any:
        """Upcast integer arrays to float64 to prevent overflow wrap.

        Backend override hook. A ulab subclass returns data unchanged —
        ulab has no float64, and accepting silent integer overflow is the
        documented trade-off on that platform.
        """
        from marple.backend_functions import is_numeric_array
        if not is_numeric_array(data) or not cls.is_int_dtype(data):
            return data
        return data.astype(np.float64)

    @classmethod
    def numeric_upcast_dtype(cls) -> Any:
        """Widest float dtype the backend supports — used as the `dtype`
        kwarg for zeros/full arrays in reduce/scan so the accumulator has
        headroom over int inputs. Desktop returns float64; ulab subclass
        returns np.float (float32) because float64 doesn't exist there.
        """
        return np.float64

    @classmethod
    def maybe_downcast(cls, data: Any, ct: float) -> Any:
        """Convert float arrays to int if all elements are close to whole numbers.

        Uses APL tolerance: |value - round(value)| <= ct * max(|value|, |round(value)|).
        Backend override hook. ulab subclass returns data unchanged — ulab's
        int widths are already narrow and the np.iinfo/int64/int32 machinery
        isn't available anyway.
        """
        if not cls.is_float_dtype(data):
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

    def __init__(self, shape: list[int], data: list[Any] | np.ndarray[Any, Any]) -> None:
        self.shape = shape
        # Storage normalisation: data is always an ndarray whose numpy
        # shape matches the platform's scalar-storage convention after init.
        #
        # Desktop numpy: APL scalars stored as rank-0 ndarrays; data.shape
        # mirrors APL shape exactly (v0.7.40 invariant).
        #
        # ulab: no 0-d arrays, so APL scalars are stored as 1-d length-1
        # while APL shape stays []. SCALAR_STORAGE_SHAPE is set at import
        # based on sys.implementation.name (pattern from pre-drop 03e7c89).
        if isinstance(data, list):
            self.data = to_array(data)
        elif isinstance(data, np.ndarray):
            # Already an ndarray (arithmetic result, upstream construction,
            # etc.) — keep as-is. The reshape at the bottom adjusts the
            # shape if needed.
            self.data = data
        elif shape == [] and SCALAR_STORAGE_SHAPE == (1,):
            # ulab scalar path: wrap a bare Python/numpy scalar as
            # length-1. ulab's np.asarray(7) would return the bare int,
            # so we construct the 1-d array explicitly.
            self.data = np.array([data])
        else:
            self.data = np.asarray(data)
        if shape == []:
            expected = SCALAR_STORAGE_SHAPE
        else:
            expected = tuple(shape)
        if self.data.shape != expected:
            self.data = self.data.reshape(expected)

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
        return scalar_item(self.data)

    def name_class(self) -> int:
        return NC_ARRAY

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, APLArray):
            return NotImplemented
        if self.shape != other.shape:
            return False
        # Mixed char/numeric arrays are never equal, even if the
        # numeric values happen to match the character codepoints.
        if is_char_array(self.data) != is_char_array(other.data):
            return False
        return bool(np.array_equal(self.data, other.data))

    @classmethod
    def array(cls, shape: list[int], data: Any) -> APLArray:
        """Factory method for creating arrays."""
        return cls(shape, data)

    @classmethod
    def scalar(cls, value: Any) -> APLArray:
        """Factory method for creating scalars.

        APL shape is `[]`. Underlying storage is 0-d on desktop numpy
        and 1-d length-1 on ulab — see __init__ for the invariant.
        """
        if isinstance(value, str):
            return cls([], str_to_char_array(value))
        return cls([], value)

    def __repr__(self) -> str:
        if self.is_scalar():
            return f"S({self.scalar_value()})"
        return f"APLArray({self.shape}, {to_list(self.data)})"

    def _dyadic(self, other: APLArray,
                f: Callable[[Any, Any], Any], bool_result: bool = False) -> APLArray:
        """Pervade a dyadic function element-wise with scalar extension."""
        a_data = to_list(self.data)
        b_data = to_list(other.data)
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
        if is_char_array(self.data) or is_char_array(other.data):
            raise DomainError(f"{op_name} is not defined on character data")

    def _reject_chars_monadic(self, op_name: str) -> None:
        """Raise DomainError if self is a character array (monadic ops)."""
        if is_char_array(self.data):
            raise DomainError(f"{op_name} is not defined on character data")

    def add(self, other: APLArray) -> APLArray:
        self._reject_chars(other, "+")
        if is_numeric_array(self.data) and is_numeric_array(other.data):
            return self._numeric_dyadic_op(other, lambda a, b: a + b, upcast=True)
        return self._dyadic(other, lambda a, b: a + b)

    def subtract(self, other: APLArray) -> APLArray:
        self._reject_chars(other, "-")
        if is_numeric_array(self.data) and is_numeric_array(other.data):
            return self._numeric_dyadic_op(other, lambda a, b: a - b, upcast=True)
        return self._dyadic(other, lambda a, b: a - b)

    def multiply(self, other: APLArray) -> APLArray:
        self._reject_chars(other, "×")
        if is_numeric_array(self.data) and is_numeric_array(other.data):
            return self._numeric_dyadic_op(other, lambda a, b: a * b, upcast=True)
        return self._dyadic(other, lambda a, b: a * b)

    def divide(self, other: APLArray) -> APLArray:
        self._reject_chars(other, "÷")
        if is_numeric_array(other.data):
            if np.any(other.data == 0):
                raise DomainError("Division by zero")
            return self._numeric_dyadic_op(other, lambda a, b: a / b)
        b_data = to_list(other.data)
        if any(x == 0 for x in b_data):
            raise DomainError("Division by zero")
        return self._dyadic(other, lambda a, b: a / b)

    def maximum(self, other: APLArray) -> APLArray:
        self._reject_chars(other, "⌈")
        if is_numeric_array(self.data) and is_numeric_array(other.data):
            return self._numeric_dyadic_op(other, lambda a, b: np.maximum(a, b))
        return self._dyadic(other, lambda a, b: max(a, b))

    def minimum(self, other: APLArray) -> APLArray:
        self._reject_chars(other, "⌊")
        if is_numeric_array(self.data) and is_numeric_array(other.data):
            return self._numeric_dyadic_op(other, lambda a, b: np.minimum(a, b))
        return self._dyadic(other, lambda a, b: min(a, b))

    def power(self, other: APLArray) -> APLArray:
        self._reject_chars(other, "*")
        if is_numeric_array(self.data) and is_numeric_array(other.data):
            return self._numeric_dyadic_op(other, lambda a, b: a ** b, upcast=True)
        return self._dyadic(other, lambda a, b: a ** b)

    def logarithm(self, other: APLArray) -> APLArray:
        self._reject_chars(other, "⍟")
        if is_numeric_array(self.data) and is_numeric_array(other.data):
            return self._numeric_dyadic_op(other, lambda a, b: np.log(b) / np.log(a))
        import math
        return self._dyadic(other, lambda a, b: math.log(b) / math.log(a))

    def residue(self, other: APLArray) -> APLArray:
        self._reject_chars(other, "|")
        if is_numeric_array(self.data) and is_numeric_array(other.data):
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
        if not is_numeric_array(self.data) or not is_numeric_array(other.data):
            ct = 0
        if is_numeric_array(self.data) and is_numeric_array(other.data):
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
        from marple.structural import reshape
        return reshape(self, other)

    def catenate(self, other: APLArray) -> APLArray:
        from marple.structural import catenate
        return catenate(self, other)

    def take(self, other: APLArray) -> APLArray:
        from marple.structural import take
        return take(self, other)

    def drop(self, other: APLArray) -> APLArray:
        from marple.structural import drop
        return drop(self, other)

    def rotate(self, other: APLArray) -> APLArray:
        from marple.structural import rotate
        return rotate(self, other)

    def rotate_first(self, other: APLArray) -> APLArray:
        from marple.structural import rotate_first
        return rotate_first(self, other)

    def encode(self, other: APLArray) -> APLArray:
        from marple.structural import encode
        return encode(self, other)

    def decode(self, other: APLArray) -> APLArray:
        from marple.structural import decode
        return decode(self, other)

    def replicate(self, other: APLArray) -> APLArray:
        from marple.structural import replicate
        return replicate(self, other)

    def replicate_first(self, other: APLArray) -> APLArray:
        from marple.structural import replicate_first
        return replicate_first(self, other)

    def expand(self, other: APLArray) -> APLArray:
        from marple.structural import expand
        return expand(self, other)

    def matrix_divide(self, other: APLArray) -> APLArray:
        from marple.structural import matrix_divide
        return matrix_divide(self, other)

    def index_of(self, other: APLArray, io: int = 1, ct: float = 0) -> APLArray:
        from marple.structural import index_of
        return index_of(self, other, io, ct)

    def membership(self, other: APLArray, ct: float = 0) -> APLArray:
        from marple.structural import membership
        return membership(self, other, ct)

    def from_array(self, other: APLArray, io: int = 1) -> APLArray:
        from marple.structural import from_array
        return from_array(self, other, io)

    def transpose_dyadic(self, other: APLArray, io: int = 1) -> APLArray:
        from marple.structural import transpose_dyadic
        return transpose_dyadic(self, other, io)

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
        indexed = list(enumerate(self.data))
        indexed.sort(key=lambda pair: pair[1])  # type: ignore[arg-type]
        return type(self).array([len(self.data)], [i + io for i, _ in indexed])

    def grade_down(self, io: int = 1) -> APLArray:
        if len(self.shape) != 1:
            raise RankError("⍒ requires a vector argument")
        indexed = list(enumerate(self.data))
        indexed.sort(key=lambda pair: pair[1], reverse=True)  # type: ignore[arg-type]
        return type(self).array([len(self.data)], [i + io for i, _ in indexed])

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
            [(-1 if x < 0 else 1 if x > 0 else 0) for x in to_list(self.data)])

    def negate(self) -> APLArray:
        self._reject_chars_monadic("monadic -")
        return self._primitive_negate()

    def _primitive_negate(self) -> APLArray:
        """Backend override hook for monadic −.

        A subclass (e.g. UlabAPLArray) may override to use a different numeric
        backend for the numeric fast path. The list fallback is backend-agnostic.
        """
        cls = type(self)
        if is_numeric_array(self.data):
            return cls.array(list(self.shape), -self.data)
        return cls.array(list(self.shape), [-x for x in to_list(self.data)])

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
        if is_numeric_array(self.data):
            if np.any(self.data == 0):
                raise DomainError("Division by zero")
            return cls.array(list(self.shape), 1.0 / self.data)
        data = to_list(self.data)
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
        if is_numeric_array(self.data):
            return type(self).array(list(self.shape), to_bool_array(1 - self.data))
        return type(self).array(list(self.shape), to_bool_array([int(not x) for x in to_list(self.data)]))

    def pi_times(self) -> APLArray:
        self._reject_chars_monadic("monadic ○")
        import math
        return type(self).array(list(self.shape), self.data * math.pi)

    def factorial(self) -> APLArray:
        self._reject_chars_monadic("monadic !")
        import math
        return type(self).array(list(self.shape), [math.gamma(x + 1) for x in to_list(self.data)])

    def shape_of(self) -> APLArray:
        return type(self).array([len(self.shape)], list(self.shape))

    def transpose(self) -> APLArray:
        # Monadic ⍉: reverse the order of axes. Per the spec,
        # ⍴⍉Y = ⌽⍴Y. For rank ≤ 1 this is identity; otherwise
        # np.transpose handles arbitrary rank.
        if len(self.shape) <= 1:
            return type(self)(list(self.shape), self.data.copy())
        return type(self)(list(reversed(self.shape)),
                        np.transpose(self.data).copy())

    def matrix_inverse(self) -> APLArray:
        from marple.structural import matrix_inverse
        return matrix_inverse(self)

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


def S(value: Any) -> APLArray:
    # Construct whichever APLArray subclass is active — NumpyAPLArray by
    # default on desktop, UlabAPLArray on the Pico. Route through the
    # backend_functions registry so subclass method overrides (e.g.
    # UlabAPLArray._numeric_dyadic_op) fire on the resulting instance.
    # Lazy import avoids an import cycle with backend_functions.
    from marple.backend_functions import get_backend_class
    return get_backend_class().scalar(value)
