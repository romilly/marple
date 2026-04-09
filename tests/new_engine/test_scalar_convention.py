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


@pytest.mark.xfail(strict=True, reason="scalar storage migration in progress")
def test_numeric_scalar_data_is_zero_dimensional() -> None:
    s = S(7)
    assert s.data.ndim == 0
    assert s.data.shape == ()


@pytest.mark.xfail(strict=True, reason="scalar storage migration in progress")
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


def test_eq_bridge_zero_d_equals_one_d_scalar() -> None:
    """A scalar APLArray with 0-d data must compare equal to one with
    1-d (1,) data when both have APL shape []. This bridge lets the
    migration progress without every test failing on the storage flip.
    """
    zero_d = APLArray([], np.asarray(7))
    one_d = APLArray([], np.array([7]))
    assert zero_d.shape == []
    assert one_d.shape == []
    assert zero_d.data.ndim == 0
    assert one_d.data.ndim == 1
    assert zero_d == one_d
    assert one_d == zero_d
