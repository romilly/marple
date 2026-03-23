"""Phase 2: Backtick glyph input in the web REPL."""


def test_backtick_rho(page):
    """Typing `r produces ⍴ in the input."""
    inp = page.locator("#input")
    inp.press("`")
    inp.press("r")
    assert "⍴" in inp.input_value()


def test_backtick_iota(page):
    """Typing `i produces ⍳."""
    inp = page.locator("#input")
    inp.press("`")
    inp.press("i")
    assert "⍳" in inp.input_value()


def test_backtick_assign(page):
    """Typing `l produces ←."""
    inp = page.locator("#input")
    inp.press("`")
    inp.press("l")
    assert "←" in inp.input_value()


def test_double_backtick(page):
    """Typing `` produces a literal backtick."""
    inp = page.locator("#input")
    inp.press("`")
    inp.press("`")
    assert "`" in inp.input_value()


def test_backtick_expression(page):
    """Type a full expression using backtick input, submit, verify result."""
    from tests.web.test_phase1_repl import submit_expr, get_session_text
    inp = page.locator("#input")
    # Type: 2+3 using backtick for nothing special, just plain keys
    # Type: `i5 which should become ⍳5
    inp.press("`")
    inp.press("i")
    inp.type("5")
    count_before = page.locator(".entry").count()
    inp.press("Enter")
    page.locator(f".entry:nth-child({count_before + 1})").wait_for(timeout=3000)
    assert "1 2 3 4 5" in get_session_text(page)


def test_backtick_visual_feedback(page):
    """After backtick, input shows visual feedback (border colour change)."""
    inp = page.locator("#input")
    inp.press("`")
    # Check that the input has the backtick-mode class
    assert "backtick" in (inp.get_attribute("class") or "")


def test_backtick_cancelled_by_escape(page):
    """Pressing Escape after backtick cancels backtick mode."""
    inp = page.locator("#input")
    inp.press("`")
    assert "backtick" in (inp.get_attribute("class") or "")
    inp.press("Escape")
    assert "backtick" not in (inp.get_attribute("class") or "")
    # Typing r should produce r, not ⍴
    inp.type("r")
    assert inp.input_value() == "r"
