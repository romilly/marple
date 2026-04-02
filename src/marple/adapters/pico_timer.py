"""PicoTimer — Timer adapter for MicroPython on Pico."""

import time

from marple.ports.timer import Timer


class PicoTimer(Timer):
    """Timer adapter using MicroPython's time module."""

    def timestamp(self) -> list[int]:
        now = time.time()
        t = time.localtime(now)
        ms = int((now % 1) * 1000)
        return [t[0], t[1], t[2], t[3], t[4], t[5], ms]

    def elapsed_ms(self) -> int:
        return time.ticks_ms()  # type: ignore[attr-defined]

    def cpu_ms(self) -> int:
        return 0

    def user_id(self) -> int:
        return 1000

    def sleep(self, seconds: float) -> float:
        t0 = time.ticks_ms()  # type: ignore[attr-defined]
        time.sleep(seconds)
        return time.ticks_diff(time.ticks_ms(), t0) / 1000  # type: ignore[attr-defined]
