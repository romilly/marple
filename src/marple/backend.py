
try:
    from typing import Any
except ImportError:
    pass

from marple.backend_functions import is_numeric_array, to_array, to_list
from marple.get_numpy import np

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
        from marple.numpy_array import NumpyArray
        return NumpyArray(shape, data)

    @classmethod
    def scalar(cls, value: Any) -> 'APLArray':
        """Factory method for creating scalars."""
        from marple.numpy_array import NumpyArray
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


def format_num(x: Any, pp: int = 10) -> str:
    """Format a number for display, using pp significant digits for floats."""
    if hasattr(x, "item"):
        x = x.item()  # type: ignore[union-attr]
    if isinstance(x, bool):
        return str(int(x))
    if isinstance(x, float):
        if x == int(x) and abs(x) < 1e15:
            n = int(x)
            return "¯" + str(abs(n)) if n < 0 else str(n)
        s = f"{x:.{pp}g}"
        if s.startswith("-"):
            s = "¯" + s[1:]
        return s
    if isinstance(x, int) and x < 0:
        return "¯" + str(abs(x))
    try:
        from decimal import Decimal
        if isinstance(x, Decimal):
            s = str(x)
            if s.startswith("-"):
                return "¯" + s[1:]
            return s
    except ImportError:
        pass
    return str(x)


def _is_char_array(arr: APLArray) -> bool:
    return len(arr.data) > 0 and all(isinstance(x, str) for x in arr.data)


def _rjust(s: str, width: int) -> str:
    if len(s) >= width:
        return s
    return " " * (width - len(s)) + s


def _format_matrix(result: APLArray, pp: int) -> str:
    """Format a rank-2 array as right-justified columns."""
    rows, cols = result.shape
    if _is_char_array(result):
        lines = []
        for r in range(rows):
            row_data = result.data[r * cols:(r + 1) * cols]
            lines.append("".join(str(x) for x in row_data))
        return "\n".join(lines)
    strs = [format_num(result.data[r * cols + c], pp) for r in range(rows) for c in range(cols)]
    col_widths = []
    for c in range(cols):
        w = max(len(strs[r * cols + c]) for r in range(rows))
        col_widths.append(w)
    lines = []
    for r in range(rows):
        parts = []
        for c in range(cols):
            parts.append(_rjust(strs[r * cols + c], col_widths[c]))
        lines.append(" ".join(parts))
    return "\n".join(lines)


def format_result(result: APLArray, env: Any = None) -> str:
    """Format an APLArray for display."""
    pp = 10
    if env is not None:
        pp_val = env.get("⎕PP")
        if pp_val is not None:
            pp = int(pp_val.data[0])
    if result.is_scalar():
        return format_num(result.data[0], pp)
    if _is_char_array(result):
        if len(result.shape) == 1:
            return "".join(str(x) for x in result.data)
        if len(result.shape) == 2:
            return _format_matrix(result, pp)
    if len(result.shape) == 1:
        return " ".join(format_num(x, pp) for x in result.data)
    if len(result.shape) == 2:
        return _format_matrix(result, pp)
    if len(result.shape) >= 3:
        slice_size = result.shape[-2] * result.shape[-1]
        num_slices = len(result.data) // slice_size
        slices = []
        for s in range(num_slices):
            start = s * slice_size
            slice_data = list(result.data[start:start + slice_size])
            slice_arr = APLArray.array([result.shape[-2], result.shape[-1]], slice_data)
            slices.append(_format_matrix(slice_arr, pp))
        return "\n\n".join(slices)
    return repr(result)


def S(value: Any) -> APLArray:
    return APLArray.scalar(value)
