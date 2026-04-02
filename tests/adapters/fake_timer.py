"""FakeTimer — test adapter for Timer port."""

from marple.ports.timer import Timer


class FakeTimer(Timer):
    """Timer adapter with controllable values for testing."""

    def __init__(self,
                 ts: list[int] | None = None,
                 elapsed: int = 0,
                 cpu: int = 0,
                 uid: int = 42,
                 sleep_elapsed: float = 0.0) -> None:
        self._ts = ts if ts is not None else [2026, 4, 2, 14, 30, 0, 0]
        self._elapsed = elapsed
        self._cpu = cpu
        self._uid = uid
        self._sleep_elapsed = sleep_elapsed

    def timestamp(self) -> list[int]:
        return list(self._ts)

    def elapsed_ms(self) -> int:
        return self._elapsed

    def cpu_ms(self) -> int:
        return self._cpu

    def user_id(self) -> int:
        return self._uid

    def sleep(self, seconds: float) -> float:
        return self._sleep_elapsed if self._sleep_elapsed else seconds
