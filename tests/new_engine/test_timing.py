"""⎕TS and ⎕AI tests."""

import time

from marple.numpy_array import APLArray, S
from marple.engine import Interpreter


class TestTS:
    def test_ts_shape(self) -> None:
        result = Interpreter(io=1).run("⎕TS")
        assert result.shape == [7]

    def test_ts_year(self) -> None:
        result = Interpreter(io=1).run("⎕TS")
        assert result.data[0] >= 2024

    def test_ts_milliseconds(self) -> None:
        """Milliseconds should be a real value 0-999."""
        result = Interpreter(io=1).run("⎕TS")
        ms = result.data[6]
        assert 0 <= int(ms) <= 999


class TestAI:
    def test_ai_shape(self) -> None:
        """⎕AI returns a 4-element vector."""
        result = Interpreter(io=1).run("⎕AI")
        assert result.shape == [4]

    def test_ai_user_id(self) -> None:
        """First element is the OS user ID."""
        import os
        result = Interpreter(io=1).run("⎕AI")
        assert int(result.data[0]) == os.getuid()

    def test_ai_compute_time(self) -> None:
        """Second element is CPU time in ms (non-negative)."""
        result = Interpreter(io=1).run("⎕AI")
        assert int(result.data[1]) >= 0

    def test_ai_connect_time_increases(self) -> None:
        """Third element is ms since session start, increases over time."""
        i = Interpreter(io=1)
        t1 = int(i.run("⎕AI").data[2])
        time.sleep(0.05)
        t2 = int(i.run("⎕AI").data[2])
        assert t2 > t1

    def test_ai_keying_time(self) -> None:
        """Fourth element is keying time (always 0 for now)."""
        result = Interpreter(io=1).run("⎕AI")
        assert int(result.data[3]) == 0

    def test_ai_for_timing(self) -> None:
        """Can subtract ⎕AI values to measure elapsed time."""
        i = Interpreter(io=1)
        i.run("t←3⌷⎕AI")
        i.run("+/⍳10000")
        elapsed = i.run("(3⌷⎕AI)-t")
        assert int(elapsed.data.item()) >= 0
