"""Canary tests for the scalar APLArray storage convention fix.

These tests assert the *desired* post-migration state: that a scalar
APLArray's underlying numpy data is 0-dimensional, matching its APL
rank-0 shape `[]`.

Each canary is marked `xfail(strict=True)` so that:
  - while the rot exists, the test fails → XFAIL (suite stays green)
  - the moment the storage flip lands and the test starts passing,
    `strict=True` turns the unexpected pass into a hard ERROR

That gives an unambiguous, test-driven signal for "the migration is
complete" without needing anyone to remember to flip a marker.
"""

import numpy as np
import pytest

from marple.engine import Interpreter
from marple.numpy_array import APLArray, S


def test_numeric_scalar_data_is_zero_dimensional() -> None:
    s = S(7)
    assert s.data.ndim == 0
    assert s.data.shape == ()


def test_char_scalar_data_is_zero_dimensional() -> None:
    # The single-char literal path goes through `Str.execute`, which
    # currently builds `APLArray([], str_to_char_array('a'))`. After the
    # migration the underlying char data must also be 0-dimensional.
    result = Interpreter(io=1).run("'a'")
    assert result.shape == []
    assert result.data.ndim == 0
    assert result.data.shape == ()


# ----------------------------------------------------------------------
# Bridge tests — __eq__ must treat 0-d and 1-d (1,) scalar storage as
# equivalent during the migration window. These tests document and lock
# in the bridge's behavior. They will be removed at Step 8 when the
# bridge itself is removed.
# ----------------------------------------------------------------------


def test_repr_handles_zero_d_scalar() -> None:
    """`__repr__` must not crash on a scalar APLArray whose underlying
    data is 0-dimensional. After Step 3, every scalar in the system
    has 0-d data; if `__repr__` blows up, every assertion failure in
    the suite becomes uninterpretable.
    """
    s = APLArray([], np.asarray(7))
    text = repr(s)
    assert isinstance(text, str)
    assert "7" in text


def test_constructor_wraps_numpy_scalar_as_zero_d_ndarray() -> None:
    """Callers must pass list or ndarray to APLArray.__init__.
    numpy scalars should be wrapped via np.asarray() at the call site,
    or use S() which handles it. This test verifies S() still produces
    a 0-d ndarray for the scalar case.
    """
    s = S(3.14)
    assert isinstance(s.data, np.ndarray)
    assert s.data.ndim == 0
    assert s.data.shape == ()
    assert float(s.data) == 3.14


def test_to_list_returns_list_for_zero_d_input() -> None:
    """`to_list` is used as a "give me an iterable" helper across the
    codebase. On a 0-d numpy array, the underlying `.tolist()` returns
    the bare scalar (e.g. `7`), NOT a list `[7]` — so any consumer
    doing `for x in to_list(...)` would silently break with a
    TypeError after the storage flip. Lock in the contract: to_list
    always returns a Python list.
    """
    from marple.backend_functions import to_list
    result = to_list(np.asarray(7))
    assert isinstance(result, list)
    assert result == [7]


def test_dyadic_handles_zero_d_scalars_both_sides() -> None:
    """The `_dyadic` helper must handle 0-d scalar operands on both
    sides. Uses `circular` (○) which has no numpy fast path and
    therefore goes straight through `_dyadic`. Test driver for the
    `_dyadic` rewrite (Step 4a of the migration).
    """
    a = APLArray([], np.asarray(1))      # selector 1 → sin
    b = APLArray([], np.asarray(0.0))    # sin(0) = 0
    result = a.circular(b)
    assert result.shape == []
    assert result == S(0.0)


def test_dyadic_handles_zero_d_left_vector_right() -> None:
    """`_dyadic` must extend a 0-d scalar left operand across a vector
    right operand. Uses `circular` (○): selector 1 → sin, applied to
    [0, 0, 0] → [0, 0, 0]."""
    a = APLArray([], np.asarray(1))                      # selector 1 → sin
    b = APLArray([3], np.asarray([0.0, 0.0, 0.0]))
    result = a.circular(b)
    assert result.shape == [3]
    assert result == APLArray.array([3], [0.0, 0.0, 0.0])


def test_dyadic_handles_vector_left_zero_d_right() -> None:
    """Mirror of the previous: vector left, 0-d scalar right."""
    import math
    a = APLArray([2], np.asarray([1, 2]))                # sin, cos
    b = APLArray([], np.asarray(0.0))
    result = a.circular(b)
    assert result.shape == [2]
    # sin(0)=0, cos(0)=1
    assert result == APLArray.array([2], [0.0, 1.0])


def test_dyadic_format_handles_zero_d_scalars() -> None:
    """`dyadic_format` (⍕) must work with 0-d scalar storage on both
    operands. The current implementation has two failure modes when
    handed a 0-d APLArray:

      1. `int(self.data[0])` for the spec → IndexError on 0-d data
      2. `[other.data[0]]` for the value → IndexError on 0-d data
         (and even after fixing that, `for v in other.data` would
         raise TypeError because numpy refuses to iterate 0-d arrays)

    Locking in the post-fix behaviour with both sides 0-d so the test
    drives both fixes in a single commit.
    """
    spec = APLArray([], np.asarray(5))
    val = APLArray([], np.asarray(7))
    result = spec.dyadic_format(val)
    # 5⍕7 with no precision: format value 7 in width 5 → "    7"
    expected_text = "    7"
    assert result.shape == [len(expected_text)]
    # Decode the uint32 char data back to a Python string for comparison.
    chars = "".join(chr(int(c)) for c in result.data.flat)
    assert chars == expected_text


