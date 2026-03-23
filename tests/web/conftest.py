import json
import pytest
import threading
import time
import urllib.request

from marple.web.server import create_server


@pytest.fixture(scope="module")
def server_url():
    """Start a MARPLE web server on a free port, yield its URL."""
    server = create_server(port=0)
    port = server.server_address[1]
    url = f"http://localhost:{port}"

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    for _ in range(50):
        try:
            resp = urllib.request.urlopen(f"{url}/health", timeout=1)
            data = json.loads(resp.read())
            if data.get("status") == "ok":
                break
        except Exception:
            time.sleep(0.1)
    else:
        raise RuntimeError("Server did not start")

    yield url

    server.shutdown()


@pytest.fixture
def page(server_url):
    """Provide a fresh Playwright browser page pointed at the server."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page()
        pg.goto(server_url)
        yield pg
        browser.close()
