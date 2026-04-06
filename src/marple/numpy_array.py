try:
    from typing import Any
except ImportError:
    pass

from marple.backend_functions import (
    is_numeric_array, maybe_upcast, to_array, to_bool_array, to_list,
)
from marple.errors import DomainError, LengthError, RankError
from marple.get_numpy import np


class APLArray:
    """APL array backed by numpy arrays."""

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
        return APLArray(shape, data)

    @classmethod
    def scalar(cls, value: Any) -> 'APLArray':
        """Factory method for creating scalars."""
        return APLArray([], [value])

    def __repr__(self) -> str:
        if self.is_scalar():
            return f"S({self.data[0]})"
        data_list = to_list(self.data) if is_numeric_array(self.data) else self.data
        return f"APLArray({self.shape}, {data_list})"

    def _dyadic(self, other: 'APLArray',
                f: Any, bool_result: bool = False) -> 'APLArray':
        """Pervade a dyadic function element-wise with scalar extension."""
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
        """Dyadic ?: deal. N?M -> N random integers from io..M without replacement."""
        import random as _random
        n = int(self.data[0])
        m = int(other.data[0])
        if n > m:
            raise LengthError(f"Deal: cannot choose {n} from {m}")
        result = _random.sample(range(io, m + io), n)
        return APLArray.array([n], result)

    # -- Dyadic structural (delegate to structural.py) --

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
        """Monadic ?: roll. ?N -> random int io..N, ?0 -> random float [0,1)."""
        import random as _random
        def roll_one(v: object) -> object:
            n = int(v)  # type: ignore[arg-type]
            return _random.random() if n == 0 else _random.randint(io, n - 1 + io)
        if self.is_scalar():
            return APLArray.scalar(roll_one(self.data[0]))
        data = np.array([roll_one(v) for v in self.data.flat])
        return APLArray(list(self.shape), data.reshape(self.shape) if self.shape else data)

    def format(self) -> 'APLArray':
        from marple.formatting import format_num
        if self.is_scalar():
            s = format_num(self.data[0])
        else:
            parts = [format_num(val) for val in self.data]
            s = " ".join(parts)
        return APLArray.array([len(s)], list(s))

    def grade_up(self, io: int = 1) -> 'APLArray':
        if len(self.shape) != 1:
            raise RankError("⍋ requires a vector argument")
        indexed = list(enumerate(self.data))
        indexed.sort(key=lambda pair: pair[1])  # type: ignore[arg-type]
        return APLArray.array([len(self.data)], [i + io for i, _ in indexed])

    def grade_down(self, io: int = 1) -> 'APLArray':
        if len(self.shape) != 1:
            raise RankError("⍒ requires a vector argument")
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
        if is_numeric_array(self.data):
            if np.any(self.data == 0):
                raise DomainError("Division by zero")
            return APLArray.array(list(self.shape), 1.0 / self.data)
        data = to_list(self.data)
        if any(x == 0 for x in data):
            raise DomainError("Division by zero")
        return APLArray.array(list(self.shape), [1 / x for x in data])

    def ceiling(self) -> 'APLArray':
        return APLArray.array(list(self.shape), np.ceil(self.data))

    def floor(self) -> 'APLArray':
        return APLArray.array(list(self.shape), np.floor(self.data))

    def exponential(self) -> 'APLArray':
        return APLArray.array(list(self.shape), np.exp(self.data))

    def natural_log(self) -> 'APLArray':
        return APLArray.array(list(self.shape), np.log(self.data))

    def absolute_value(self) -> 'APLArray':
        return APLArray.array(list(self.shape), abs(self.data))

    def logical_not(self) -> 'APLArray':
        if is_numeric_array(self.data):
            return APLArray.array(list(self.shape), to_bool_array(1 - self.data))
        return APLArray.array(list(self.shape), to_bool_array([int(not x) for x in to_list(self.data)]))

    def pi_times(self) -> 'APLArray':
        import math
        return APLArray.array(list(self.shape), self.data * math.pi)

    def factorial(self) -> 'APLArray':
        import math
        return APLArray.array(list(self.shape), [math.gamma(x + 1) for x in to_list(self.data)])

    def shape_of(self) -> 'APLArray':
        return APLArray.array([len(self.shape)], list(self.shape))

    def transpose(self) -> 'APLArray':
        if len(self.shape) <= 1:
            return self
        if len(self.shape) != 2:
            raise RankError("Transpose currently supports only rank-2 arrays")
        return APLArray([self.shape[1], self.shape[0]], self.data.T.copy())

    def matrix_inverse(self) -> 'APLArray':
        from marple.structural import matrix_inverse
        return matrix_inverse(self)

    def reverse(self) -> 'APLArray':
        if is_numeric_array(self.data):
            return APLArray(list(self.shape), np.flip(self.data, axis=-1).copy())
        if len(self.shape) <= 1:
            return APLArray.array(list(self.shape), list(reversed(self.data)))
        # Character matrix: reverse each row
        row_len = self.shape[-1]
        data = self.data
        result: list[object] = []
        for i in range(0, len(data), row_len):
            result.extend(reversed(data[i:i + row_len]))
        return APLArray.array(list(self.shape), result)

    def reverse_first(self) -> 'APLArray':
        if is_numeric_array(self.data):
            return APLArray(list(self.shape), np.flip(self.data, axis=0).copy())
        return APLArray.array(list(self.shape), list(reversed(self.data)))

    def ravel(self) -> 'APLArray':
        flat = self.data.flatten() if is_numeric_array(self.data) else self.data
        return APLArray(  [len(flat)], flat)


def S(value: Any) -> APLArray:
    return APLArray.scalar(value)
