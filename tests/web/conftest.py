import asyncio
import json
import threading
import time
import urllib.request

import pytest
from aiohttp import web

from marple.web.server import create_app


@pytest.fixture(scope="module")
def server_url():
    """Start a MARPLE aiohttp server on a free port, yield its URL."""
    app = create_app()
    loop = asyncio.new_event_loop()

    runner = web.AppRunner(app)
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, "localhost", 0)
    loop.run_until_complete(site.start())

    # Extract the actual port
    sockets = site._server.sockets  # type: ignore[union-attr]
    port = sockets[0].getsockname()[1]
    url = f"http://localhost:{port}"

    thread = threading.Thread(target=loop.run_forever, daemon=True)
    thread.start()

    # Wait for server to be ready
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

    loop.call_soon_threadsafe(loop.stop)


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
