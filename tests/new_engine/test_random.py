"""Random function tests — new engine."""

from marple.arraymodel import APLArray, S
from marple.engine import Interpreter


class TestRoll:
    def test_roll_returns_float(self) -> None:
        result = Interpreter(io=1).run("?0")
        assert isinstance(result.data[0], float)
        assert 0.0 <= result.data[0] < 1.0

    def test_roll_integer(self) -> None:
        result = Interpreter(io=1).run("?6")
        val = int(result.data[0])
        assert 1 <= val <= 6

    def test_roll_vector(self) -> None:
        result = Interpreter(io=1).run("?6 6 6")
        assert result.shape == [3]
        for v in result.data:
            assert 1 <= int(v) <= 6


class TestDeal:
    def test_deal(self) -> None:
        result = Interpreter(io=1).run("3?10")
        assert result.shape == [3]
        values = [int(v) for v in result.data]
        assert len(set(values)) == 3
        assert all(1 <= v <= 10 for v in values)

    def test_deal_io0(self) -> None:
        result = Interpreter(io=0).run("3?10")
        assert result.shape == [3]
        values = [int(v) for v in result.data]
        assert len(set(values)) == 3
        assert all(0 <= v <= 9 for v in values)
