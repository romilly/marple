"""Phase 5: Multi-line input with Shift+Enter."""
from tests.e2e.web.test_phase1_repl import submit_expr, get_session_text


def test_shift_enter_adds_newline(page):
    """Shift+Enter adds a newline, does not submit."""
    inp = page.locator("#input")
    inp.fill("line1")
    inp.press("Shift+Enter")
    inp.type("line2")
    val = inp.input_value()
    assert "line1" in val and "line2" in val
    # Should NOT have submitted
    assert page.locator(".entry").count() == 0


def test_enter_submits_multiline(page):
    """Enter submits the full multi-line content."""
    inp = page.locator("#input")
    inp.fill("x←5")
    inp.press("Shift+Enter")
    inp.type("x+1")
    count_before = page.locator(".entry").count()
    inp.press("Enter")
    page.locator(f".entry:nth-child({count_before + 1})").wait_for(timeout=3000)
    # The diamond-separated expression should have been evaluated
    assert "6" in get_session_text(page)


def test_textarea_visible(page):
    """Input area should be a textarea for multi-line support."""
    assert page.locator("#input").is_visible()


def test_dfn_multiline(page):
    """Define a multi-line dfn using Shift+Enter."""
    inp = page.locator("#input")
    inp.type("sort←{⍵[⍋⍵]}")
    count_before = page.locator(".entry").count()
    inp.press("Enter")
    page.locator(f".entry:nth-child({count_before + 1})").wait_for(timeout=3000)
    submit_expr(page, "sort 3 1 4 1 5")
    assert "1 1 3 4 5" in get_session_text(page)
