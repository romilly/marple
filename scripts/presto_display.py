"""LCD display mirror for the Pimoroni Presto.

Renders MARPLE REPL input/output on the 480x480 touchscreen using
the APL bitmap font. Optional — imported with try/except
in pico_eval.py so it's a no-op on non-Presto boards.
"""


class PrestoDisplay:
    """Manages the Presto LCD as a scrolling APL terminal."""

    def __init__(self) -> None:
        from presto import Presto  # type: ignore[import-not-found]
        import apl_font  # type: ignore[import-not-found]
        self.presto = Presto(full_res=True)
        self.display = self.presto.display
        self.font = apl_font
        self.y = 4
        self.max_y = 480 - apl_font.CELL_H
        self.bg = self.display.create_pen(20, 20, 30)
        self.input_pen = self.display.create_pen(200, 200, 220)
        self.output_pen = self.display.create_pen(200, 220, 200)
        self.error_pen = self.display.create_pen(220, 100, 100)
        self.banner_pen = self.display.create_pen(100, 200, 100)
        self.display.set_pen(self.bg)
        self.display.clear()
        self.presto.update()

    def _show_line(self, text: str, pen: int) -> None:
        if self.y > self.max_y:
            self._scroll()
        self.display.set_pen(pen)
        self.font.draw_text(self.display, text, 4, self.y)
        self.y += self.font.CELL_H
        self.presto.update()

    def show_input(self, expr: str) -> None:
        self._show_line("      " + expr, self.input_pen)

    def show_output(self, text: str) -> None:
        for line in text.split("\n"):
            self._show_line(line, self.output_pen)

    def show_error(self, text: str) -> None:
        self._show_line(text, self.error_pen)

    def show_banner(self, text: str) -> None:
        self._show_line(text, self.banner_pen)

    def _scroll(self) -> None:
        self.display.set_pen(self.bg)
        self.display.clear()
        self.y = 4
