"""Phase 4: Session history with up/down arrow keys."""
from tests.web.test_phase1_repl import submit_expr


def test_up_arrow_recalls_last(page):
    """Up arrow recalls the most recent expression."""
    submit_expr(page, "2+3")
    page.locator("#input").press("ArrowUp")
    assert page.locator("#input").input_value() == "2+3"


def test_up_arrow_multiple(page):
    """Up arrow cycles through history in reverse order."""
    submit_expr(page, "1+1")
    submit_expr(page, "2+2")
    submit_expr(page, "3+3")
    inp = page.locator("#input")
    inp.press("ArrowUp")
    assert inp.input_value() == "3+3"
    inp.press("ArrowUp")
    assert inp.input_value() == "2+2"
    inp.press("ArrowUp")
    assert inp.input_value() == "1+1"


def test_up_arrow_stops_at_oldest(page):
    """Up arrow at the oldest entry stays there."""
    submit_expr(page, "1+1")
    submit_expr(page, "2+2")
    inp = page.locator("#input")
    inp.press("ArrowUp")
    inp.press("ArrowUp")
    inp.press("ArrowUp")  # past the oldest
    assert inp.input_value() == "1+1"


def test_down_arrow_moves_forward(page):
    """Down arrow moves forward in history."""
    submit_expr(page, "1+1")
    submit_expr(page, "2+2")
    submit_expr(page, "3+3")
    inp = page.locator("#input")
    inp.press("ArrowUp")
    inp.press("ArrowUp")
    inp.press("ArrowUp")
    assert inp.input_value() == "1+1"
    inp.press("ArrowDown")
    assert inp.input_value() == "2+2"
    inp.press("ArrowDown")
    assert inp.input_value() == "3+3"


def test_down_arrow_past_newest_clears(page):
    """Down arrow past the newest entry clears the input."""
    submit_expr(page, "1+1")
    inp = page.locator("#input")
    inp.press("ArrowUp")
    assert inp.input_value() == "1+1"
    inp.press("ArrowDown")
    assert inp.input_value() == ""


def test_new_submission_resets_pointer(page):
    """Submitting a new expression resets the history pointer."""
    submit_expr(page, "1+1")
    submit_expr(page, "2+2")
    inp = page.locator("#input")
    inp.press("ArrowUp")
    assert inp.input_value() == "2+2"
    # Submit something new
    submit_expr(page, "9+9")
    inp.press("ArrowUp")
    assert inp.input_value() == "9+9"
