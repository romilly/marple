from marple.arraymodel import APLArray, S
from marple.errors import LengthError
from marple.interpreter import interpret
import pytest


class TestRoll:
    def test_roll_deterministic(self) -> None:
        env: dict[str, object] = {}
        interpret("⎕RL←42", env)
        r1 = interpret("?6", env)
        interpret("⎕RL←42", env)
        r2 = interpret("?6", env)
        assert r1 == r2

    def test_roll_in_range(self) -> None:
        env: dict[str, object] = {}
        interpret("⎕RL←42", env)
        for _ in range(20):
            result = interpret("?6", env)
            v = result.data[0]
            assert 1 <= v <= 6

    def test_roll_zero_gives_float(self) -> None:
        env: dict[str, object] = {}
        interpret("⎕RL←42", env)
        result = interpret("?0", env)
        v = result.data[0]
        assert isinstance(v, float)
        assert 0 <= v < 1

    def test_roll_pervades(self) -> None:
        env: dict[str, object] = {}
        interpret("⎕RL←42", env)
        result = interpret("?6 6 6", env)
        assert result.shape == [3]
        for v in result.data:
            assert 1 <= v <= 6

    def test_roll_respects_io(self) -> None:
        env: dict[str, object] = {}
        interpret("⎕IO←0", env)
        interpret("⎕RL←42", env)
        for _ in range(20):
            result = interpret("?6", env)
            v = result.data[0]
            assert 0 <= v <= 5


class TestDeal:
    def test_deal_length(self) -> None:
        env: dict[str, object] = {}
        interpret("⎕RL←42", env)
        result = interpret("5?10", env)
        assert result.shape == [5]

    def test_deal_distinct(self) -> None:
        env: dict[str, object] = {}
        interpret("⎕RL←42", env)
        result = interpret("5?10", env)
        values = list(result.data)
        assert len(set(values)) == 5

    def test_deal_in_range(self) -> None:
        env: dict[str, object] = {}
        interpret("⎕RL←42", env)
        result = interpret("5?10", env)
        for v in result.data:
            assert 1 <= v <= 10

    def test_deal_deterministic(self) -> None:
        env: dict[str, object] = {}
        interpret("⎕RL←42", env)
        r1 = interpret("5?52", env)
        interpret("⎕RL←42", env)
        r2 = interpret("5?52", env)
        assert r1 == r2

    def test_deal_respects_io(self) -> None:
        env: dict[str, object] = {}
        interpret("⎕IO←0", env)
        interpret("⎕RL←42", env)
        result = interpret("5?10", env)
        for v in result.data:
            assert 0 <= v <= 9

    def test_deal_n_exceeds_m_error(self) -> None:
        env: dict[str, object] = {}
        with pytest.raises(LengthError):
            interpret("10?5", env)


class TestQuadRL:
    def test_default_rl(self) -> None:
        assert interpret("⎕RL") == S(0)

    def test_set_rl(self) -> None:
        env: dict[str, object] = {}
        interpret("⎕RL←123", env)
        assert interpret("⎕RL", env) == S(123)
