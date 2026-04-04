"""Random function tests — new engine."""

import pytest

from marple.numpy_array import APLArray, S
from marple.engine import Interpreter
from marple.errors import LengthError


class TestRoll:
    def test_roll_returns_float(self) -> None:
        result = Interpreter(io=1).run("?0")
        assert isinstance(result.data[0], float)
        assert 0.0 <= result.data[0] < 1.0

    def test_roll_integer(self) -> None:
        result = Interpreter(io=1).run("?6")
        val = int(result.data[0])
        assert 1 <= val <= 6

    def test_roll_deterministic(self) -> None:
        i = Interpreter(io=1)
        i.run("⎕RL←42")
        r1 = i.run("?6")
        i.run("⎕RL←42")
        r2 = i.run("?6")
        assert r1 == r2

    def test_roll_in_range(self) -> None:
        i = Interpreter(io=1)
        i.run("⎕RL←42")
        for _ in range(20):
            result = i.run("?6")
            v = result.data[0]
            assert 1 <= v <= 6

    def test_roll_vector(self) -> None:
        result = Interpreter(io=1).run("?6 6 6")
        assert result.shape == [3]
        for v in result.data:
            assert 1 <= int(v) <= 6

    def test_roll_respects_io(self) -> None:
        i = Interpreter(io=0)
        i.run("⎕RL←42")
        for _ in range(20):
            result = i.run("?6")
            v = result.data[0]
            assert 0 <= v <= 5


class TestDeal:
    def test_deal(self) -> None:
        result = Interpreter(io=1).run("3?10")
        assert result.shape == [3]
        values = [int(v) for v in result.data]
        assert len(set(values)) == 3
        assert all(1 <= v <= 10 for v in values)

    def test_deal_length(self) -> None:
        i = Interpreter(io=1)
        i.run("⎕RL←42")
        result = i.run("5?10")
        assert result.shape == [5]

    def test_deal_distinct(self) -> None:
        i = Interpreter(io=1)
        i.run("⎕RL←42")
        result = i.run("5?10")
        values = list(result.data)
        assert len(set(values)) == 5

    def test_deal_in_range(self) -> None:
        i = Interpreter(io=1)
        i.run("⎕RL←42")
        result = i.run("5?10")
        for v in result.data:
            assert 1 <= v <= 10

    def test_deal_deterministic(self) -> None:
        i = Interpreter(io=1)
        i.run("⎕RL←42")
        r1 = i.run("5?52")
        i.run("⎕RL←42")
        r2 = i.run("5?52")
        assert r1 == r2

    def test_deal_io0(self) -> None:
        result = Interpreter(io=0).run("3?10")
        assert result.shape == [3]
        values = [int(v) for v in result.data]
        assert len(set(values)) == 3
        assert all(0 <= v <= 9 for v in values)

    def test_deal_n_exceeds_m_error(self) -> None:
        with pytest.raises(LengthError):
            Interpreter(io=1).run("10?5")


class TestQuadRL:
    def test_default_rl(self) -> None:
        assert Interpreter(io=1).run("⎕RL") == S(1)

    def test_set_rl(self) -> None:
        i = Interpreter(io=1)
        i.run("⎕RL←123")
        assert i.run("⎕RL") == S(123)
