"""PrideConsole — Console adapter for PRIDE web IDE with WebSocket input."""

import threading

from marple.ports.console import Console


class PrideConsole(Console):
    """Console adapter that buffers output and supports threaded input requests.

    When read_line is called (from an executor running in a thread),
    it signals that input is needed and blocks until provide_input is called
    from the async WebSocket handler.
    """

    def __init__(self) -> None:
        self._output: list[str] = []
        self._prompt_value: str = ""
        self._input_value: str | None = None
        self._prompt_ready = threading.Event()
        self._input_ready = threading.Event()

    def read_line(self, prompt: str) -> str | None:
        """Block until input is provided via provide_input()."""
        self._prompt_value = prompt
        self._input_ready.clear()
        self._prompt_ready.set()
        self._input_ready.wait()
        return self._input_value

    def write(self, text: str) -> None:
        self._output.append(text)

    def writeln(self, text: str) -> None:
        self._output.append(text + "\n")

    def provide_input(self, text: str) -> None:
        """Called from the async handler when the client sends input."""
        self._input_value = text
        self._input_ready.set()

    def wait_for_prompt(self, timeout: float = 0.1) -> str | None:
        """Wait for an input request. Returns prompt string or None on timeout."""
        if self._prompt_ready.wait(timeout):
            self._prompt_ready.clear()
            return self._prompt_value
        return None

    def clear(self) -> None:
        """Clear the output buffer."""
        self._output.clear()

    @property
    def output(self) -> str:
        return "".join(self._output)

    @property
    def output_lines(self) -> list[str]:
        text = self.output
        if text.endswith("\n"):
            text = text[:-1]
        return text.split("\n") if text else []
