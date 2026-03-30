"""End-to-end Playwright tests for PRIDE web IDE."""

import subprocess
import time

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def pride_server():
    """Start PRIDE server for testing."""
    proc = subprocess.Popen(
        ["python", "-m", "marple.web.server", "--port", "18888"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(1)  # wait for server startup
    yield "http://localhost:18888"
    proc.terminate()
    proc.wait(timeout=5)


def _submit(page: Page, expr: str) -> None:
    """Type an expression and press Enter."""
    inp = page.locator("#input")
    inp.fill(expr)
    inp.press("Enter")


def _last_output(page: Page) -> str:
    """Return the text of the last output element in the session."""
    outputs = page.locator("#session pre.output")
    outputs.last.wait_for(timeout=5000)
    return outputs.last.text_content() or ""


def _last_entry_text(page: Page) -> str:
    """Return all text from the last entry div."""
    entries = page.locator("#session .entry")
    entries.last.wait_for(timeout=5000)
    return entries.last.text_content() or ""


class TestVersionDisplay:
    """Verify that PRIDE shows the version in the page title."""

    def test_title_contains_version(self, page: Page, pride_server: str) -> None:
        from marple import __version__
        page.goto(pride_server)
        page.wait_for_function(
            "document.title.includes('MARPLE v')",
            timeout=5000,
        )
        assert __version__ in page.title()


class TestFirstEval:
    """Verify that the first eval in a session works correctly."""

    def test_first_eval_shows_output(self, page: Page, pride_server: str) -> None:
        page.goto(pride_server)
        page.wait_for_selector("#ws-status", state="attached")
        # Wait for WebSocket to connect
        page.wait_for_function("document.getElementById('ws-status').textContent === 'connected'")

        _submit(page, "2+3")
        assert_text = _last_output(page)
        assert "5" in assert_text

    def test_second_eval_also_works(self, page: Page, pride_server: str) -> None:
        page.goto(pride_server)
        page.wait_for_function("document.getElementById('ws-status').textContent === 'connected'")

        _submit(page, "2+3")
        _last_output(page)  # wait for first result

        _submit(page, "3×4")
        # Wait for a second output to appear
        page.locator("#session pre.output").nth(1).wait_for(timeout=5000)
        assert "12" in page.locator("#session pre.output").nth(1).text_content()

    def test_quad_assign_output(self, page: Page, pride_server: str) -> None:
        page.goto(pride_server)
        page.wait_for_function("document.getElementById('ws-status').textContent === 'connected'")

        _submit(page, "⎕←42")
        assert "42" in _last_output(page)


class TestQuadInput:
    """Test ⎕ input in PRIDE."""

    def test_quad_input_evaluates_and_assigns(self, page: Page, pride_server: str) -> None:
        page.goto(pride_server)
        page.wait_for_function("document.getElementById('ws-status').textContent === 'connected'")

        _submit(page, "y←⎕")

        # Wait for input mode — input should show ⎕: prompt
        inp = page.locator("#input")
        expect(inp).to_have_value("⎕:", timeout=5000)

        # Type the response after the prompt
        inp.press("End")
        inp.type("2+3")
        inp.press("Enter")

        # Wait for the assignment to complete
        page.locator("#session .entry").nth(0).wait_for(timeout=5000)

        # Now check the value was assigned correctly
        _submit(page, "y")
        page.locator("#session .entry").nth(1).wait_for(timeout=5000)
        output = _last_output(page)
        assert "5" in output, f"Expected '5' in session output, got: {output!r}"

    def test_quad_input_iota(self, page: Page, pride_server: str) -> None:
        page.goto(pride_server)
        page.wait_for_function("document.getElementById('ws-status').textContent === 'connected'")

        # Check actual ⎕IO to know the expected result
        _submit(page, "⎕IO")
        io_output = _last_output(page)
        if "0" in io_output:
            expected = "0 1 2"
        else:
            expected = "1 2 3"

        _submit(page, "y←⎕")
        inp = page.locator("#input")
        expect(inp).to_have_value("⎕:", timeout=5000)
        inp.press("End")
        inp.type("⍳3")
        inp.press("Enter")

        page.locator("#session .entry").nth(1).wait_for(timeout=5000)

        _submit(page, "y")
        page.locator("#session .entry").nth(2).wait_for(timeout=5000)
        output = _last_output(page)
        assert expected in output, f"Expected '{expected}' in session output, got: {output!r}"


class TestQuoteQuadInput:
    """Test ⍞ input in PRIDE."""

    def test_quote_quad_assign_returns_prompt_plus_response(self, page: Page, pride_server: str) -> None:
        page.goto(pride_server)
        page.wait_for_function("document.getElementById('ws-status').textContent === 'connected'")

        _submit(page, "a←⍞←'Name: '")

        # Wait for input mode — input should show the prompt
        inp = page.locator("#input")
        expect(inp).to_have_value("Name: ", timeout=5000)

        # Type the response
        inp.press("End")
        inp.type("Romilly")
        inp.press("Enter")

        # Wait for assignment to complete
        page.locator("#session .entry").nth(0).wait_for(timeout=5000)

        # Check the value — should be prompt + response
        _submit(page, "a")
        output = _last_output(page)
        assert "Romilly" in output, f"Expected 'Romilly' in session output, got: {output}"
