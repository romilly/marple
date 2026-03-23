"""Phase 7: Workspace panel showing variables and functions."""
from tests.web.test_phase1_repl import submit_expr, get_session_text


def test_workspace_panel_visible(page):
    """Workspace panel is visible on page load."""
    assert page.locator("#workspace").is_visible()


def test_variable_appears(page):
    """Define a variable — it appears in the workspace panel."""
    submit_expr(page, "X←42")
    page.wait_for_timeout(500)
    text = page.locator("#workspace").inner_text()
    assert "X" in text


def test_variable_shows_shape(page):
    """Workspace panel shows variable shape."""
    submit_expr(page, "M←3 4⍴⍳12")
    page.wait_for_timeout(500)
    text = page.locator("#workspace").inner_text()
    assert "M" in text
    assert "3 4" in text


def test_function_appears(page):
    """Define a function — it appears in the workspace panel."""
    submit_expr(page, "double←{⍵+⍵}")
    page.wait_for_timeout(500)
    text = page.locator("#workspace").inner_text()
    assert "double" in text


def test_clear_empties_panel(page):
    """After )clear, workspace panel is empty."""
    submit_expr(page, "X←1")
    page.wait_for_timeout(500)
    submit_expr(page, ")clear")
    page.wait_for_timeout(500)
    text = page.locator("#workspace").inner_text()
    assert "X" not in text


def test_click_variable_inserts(page):
    """Click a variable name in the panel — it appears in the input."""
    submit_expr(page, "myvar←99")
    page.wait_for_timeout(500)
    page.locator("#workspace .ws-item", has_text="myvar").click()
    assert "myvar" in page.locator("#input").input_value()
