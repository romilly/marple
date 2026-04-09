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

import pytest

from marple.engine import Interpreter
from marple.numpy_array import S


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
