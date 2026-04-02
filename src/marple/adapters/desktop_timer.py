"""DesktopTimer — Timer adapter for CPython."""

import os
import time

from marple.ports.timer import Timer


class DesktopTimer(Timer):
    """Timer adapter using CPython's time and resource modules."""

    def __init__(self) -> None:
        self._start_time = time.time()

    def timestamp(self) -> list[int]:
        now = time.time()
        t = time.localtime(now)
        ms = int((now % 1) * 1000)
        return [t[0], t[1], t[2], t[3], t[4], t[5], ms]

    def elapsed_ms(self) -> int:
        return int((time.time() - self._start_time) * 1000)

    def cpu_ms(self) -> int:
        try:
            import resource
            return int(resource.getrusage(resource.RUSAGE_SELF).ru_utime * 1000)
        except (ImportError, AttributeError):
            return 0

    def user_id(self) -> int:
        try:
            return os.getuid()
        except AttributeError:
            return 1000

    def sleep(self, seconds: float) -> float:
        t0 = time.time()
        time.sleep(seconds)
        return time.time() - t0
