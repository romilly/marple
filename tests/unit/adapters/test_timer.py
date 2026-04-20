"""Tests for Timer abstraction — ⎕TS, ⎕AI, ⎕DL via FakeTimer."""

from marple.ports.array import APLArray, S
from marple.engine import Interpreter
from tests.adapters.fake_timer import FakeTimer


class TestQuadTSWithTimer:
    def test_ts_returns_fake_timestamp(self) -> None:
        timer = FakeTimer(ts=[2026, 4, 2, 14, 30, 45, 123])
        interp = Interpreter(io=1, timer=timer)
        result = interp.run("⎕TS")
        assert result == APLArray.array([7], [2026, 4, 2, 14, 30, 45, 123])


class TestQuadAIWithTimer:
    def test_ai_returns_fake_values(self) -> None:
        timer = FakeTimer(uid=99, cpu=500, elapsed=12345)
        interp = Interpreter(io=1, timer=timer)
        result = interp.run("⎕AI")
        assert result.data[0] == 99    # user ID
        assert result.data[1] == 500   # CPU ms
        assert result.data[2] == 12345 # elapsed ms


class TestQuadDLWithTimer:
    def test_dl_returns_fake_elapsed(self) -> None:
        timer = FakeTimer(sleep_elapsed=0.05)
        interp = Interpreter(io=1, timer=timer)
        result = interp.run("⎕DL 0.01")
        assert result == S(0.05)
