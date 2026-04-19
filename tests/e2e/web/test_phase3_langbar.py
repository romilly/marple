"""Phase 3: Language bar in the web REPL."""
from tests.e2e.web.test_phase1_repl import submit_expr, get_session_text


def test_language_bar_visible(page):
    """Language bar is visible on page load."""
    assert page.locator("#langbar").is_visible()


def test_click_rho(page):
    """Click ⍴ button inserts ⍴ into input."""
    page.locator("#langbar button", has_text="⍴").click()
    assert "⍴" in page.locator("#input").input_value()


def test_click_iota(page):
    """Click ⍳ button inserts ⍳ into input."""
    page.locator("#langbar button", has_text="⍳").click()
    assert "⍳" in page.locator("#input").input_value()


def test_click_multiple(page):
    """Click multiple glyphs, they appear in sequence."""
    page.locator("#langbar button", has_text="⍳").click()
    page.locator("#langbar button", has_text="⍴").click()
    val = page.locator("#input").input_value()
    assert "⍳" in val and "⍴" in val


def test_tooltip_on_hover(page):
    """Hover over a glyph shows tooltip with name."""
    btn = page.locator("#langbar button", has_text="⍴")
    title = btn.get_attribute("title")
    assert title is not None
    assert "Rho" in title or "rho" in title or "⍴" in title


def test_click_then_submit(page):
    """Click glyphs to build expression, submit, verify result."""
    page.locator("#langbar button", has_text="⍳").click()
    page.locator("#input").type("5")
    count_before = page.locator(".entry").count()
    page.locator("#input").press("Enter")
    page.locator(f".entry:nth-child({count_before + 1})").wait_for(timeout=3000)
    assert "1 2 3 4 5" in get_session_text(page)
