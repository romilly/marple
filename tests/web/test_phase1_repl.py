import json
import urllib.request


def submit_expr(page, text):
    """Type an expression and press Enter, wait for response."""
    input_el = page.locator("#input")
    input_el.fill(text)
    count_before = page.locator(".entry").count()
    input_el.press("Enter")
    page.locator(f".entry:nth-child({count_before + 1})").wait_for(timeout=3000)


def get_session_text(page):
    """Get all text from the session log."""
    return page.locator("#session").inner_text()


def test_health_endpoint(server_url):
    """The /health endpoint returns ok."""
    resp = urllib.request.urlopen(f"{server_url}/health")
    data = json.loads(resp.read())
    assert data == {"status": "ok"}


def test_page_loads(page):
    """The frontend loads and shows an input field."""
    assert page.locator("#input").is_visible()


def test_simple_arithmetic(page):
    """Submit 2+3, expect 5 in the output."""
    submit_expr(page, "2+3")
    assert "5" in get_session_text(page)


def test_iota(page):
    """Submit ⍳5, expect 1 2 3 4 5."""
    submit_expr(page, "⍳5")
    assert "1 2 3 4 5" in get_session_text(page)


def test_domain_error(page):
    """Submit 1÷0, expect a DOMAIN ERROR."""
    submit_expr(page, "1÷0")
    text = get_session_text(page)
    assert "DOMAIN ERROR" in text
    assert page.locator("pre.error").count() > 0


def test_state_persists(page):
    """Define a variable, then use it in the next expression."""
    submit_expr(page, "X←42")
    submit_expr(page, "X+1")
    assert "43" in get_session_text(page)


def test_matrix_output(page):
    """Define and display a matrix. Check output is pre-formatted."""
    submit_expr(page, "M←3 4⍴⍳12")
    submit_expr(page, "M")
    text = get_session_text(page)
    assert "1" in text and "12" in text
    assert page.locator("pre.output").count() > 0


def test_empty_input_does_nothing(page):
    """Pressing Enter with empty input should not add anything."""
    count_before = page.locator(".entry").count()
    page.locator("#input").press("Enter")
    page.wait_for_timeout(300)
    count_after = page.locator(".entry").count()
    assert count_before == count_after


def test_system_command_vars(page):
    """Define variables, then )vars should list them."""
    submit_expr(page, "A←1")
    submit_expr(page, "B←2")
    submit_expr(page, ")vars")
    text = get_session_text(page)
    assert "A" in text and "B" in text


def test_system_command_clear(page):
    """After )clear, the response should confirm clearing."""
    submit_expr(page, "X←99")
    submit_expr(page, ")clear")
    text = get_session_text(page)
    assert "CLEAR" in text.upper()


def test_assignment_no_visible_output(page):
    """An assignment like X←5 should show the input but no output."""
    submit_expr(page, "X←5")
    entry = page.locator(".entry").last
    assert entry.locator("pre.input").count() == 1
    assert entry.locator("pre.output").count() == 0
    assert entry.locator("pre.error").count() == 0


def test_dfn_definition_and_use(page):
    """Define a dfn and then call it."""
    submit_expr(page, "double←{⍵+⍵}")
    submit_expr(page, "double 21")
    assert "42" in get_session_text(page)


def test_input_clears_after_submit(page):
    """The input field should be empty after submission."""
    page.locator("#input").fill("2+3")
    count_before = page.locator(".entry").count()
    page.locator("#input").press("Enter")
    page.locator(f".entry:nth-child({count_before + 1})").wait_for(timeout=3000)
    assert page.locator("#input").input_value() == ""


def test_multiple_expressions_accumulate(page):
    """Multiple submissions should all appear in the session log."""
    submit_expr(page, "1+1")
    submit_expr(page, "2+2")
    submit_expr(page, "3+3")
    assert page.locator(".entry").count() >= 3
    text = get_session_text(page)
    assert "2" in text and "4" in text and "6" in text
