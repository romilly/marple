"""Tests for WebSocket communication."""

import pytest

from marple.web.server import create_app


@pytest.fixture
def app():
    return create_app()


async def test_ws_eval(aiohttp_client, app):
    client = await aiohttp_client(app)
    ws = await client.ws_connect("/ws")
    await ws.send_json({"type": "eval", "expr": "2+3"})
    msg = await ws.receive_json()
    assert msg["type"] == "result"
    assert "5" in msg["html"]
    await ws.close()


async def test_ws_eval_iota(aiohttp_client, app):
    client = await aiohttp_client(app)
    ws = await client.ws_connect("/ws")
    await ws.send_json({"type": "eval", "expr": "⍳5"})
    msg = await ws.receive_json()
    assert msg["type"] == "result"
    assert "1 2 3 4 5" in msg["html"]
    await ws.close()


async def test_ws_eval_sends_workspace(aiohttp_client, app):
    client = await aiohttp_client(app)
    ws = await client.ws_connect("/ws")
    await ws.send_json({"type": "eval", "expr": "x←42"})
    msg1 = await ws.receive_json()
    assert msg1["type"] == "result"
    msg2 = await ws.receive_json()
    assert msg2["type"] == "workspace"
    assert "x" in msg2["html"]
    await ws.close()


async def test_ws_system_command(aiohttp_client, app):
    client = await aiohttp_client(app)
    ws = await client.ws_connect("/ws")
    await ws.send_json({"type": "eval", "expr": "v←1 2 3"})
    await ws.receive_json()  # result
    await ws.receive_json()  # workspace
    await ws.send_json({"type": "system", "cmd": ")vars"})
    msg = await ws.receive_json()
    assert msg["type"] == "result"
    assert "v" in msg["html"]
    await ws.close()


async def test_ws_error(aiohttp_client, app):
    client = await aiohttp_client(app)
    ws = await client.ws_connect("/ws")
    await ws.send_json({"type": "eval", "expr": "1÷0"})
    msg = await ws.receive_json()
    assert msg["type"] == "result"
    assert "DOMAIN ERROR" in msg["html"]
    await ws.close()


async def test_ws_bad_message(aiohttp_client, app):
    client = await aiohttp_client(app)
    ws = await client.ws_connect("/ws")
    await ws.send_str("not json")
    msg = await ws.receive_json()
    assert msg["type"] == "error"
    await ws.close()


async def test_ws_unknown_type(aiohttp_client, app):
    client = await aiohttp_client(app)
    ws = await client.ws_connect("/ws")
    await ws.send_json({"type": "bogus"})
    msg = await ws.receive_json()
    assert msg["type"] == "error"
    await ws.close()


async def test_ws_mode_switch_local(aiohttp_client, app):
    client = await aiohttp_client(app)
    ws = await client.ws_connect("/ws")
    await ws.send_json({"type": "mode", "mode": "local"})
    msg = await ws.receive_json()
    assert msg["type"] == "mode_changed"
    assert msg["mode"] == "local"
    await ws.close()


async def test_ws_mode_switch_pico_no_connection(aiohttp_client, app):
    """Switching to pico mode without a Pico connected gives an error."""
    client = await aiohttp_client(app)
    ws = await client.ws_connect("/ws")
    await ws.send_json({"type": "mode", "mode": "pico"})
    msg = await ws.receive_json()
    assert msg["type"] == "error"
    assert "pico" in msg["message"].lower() or "not" in msg["message"].lower()
    await ws.close()


class FakePicoConnection:
    """Mock PicoConnection for testing."""

    def __init__(self) -> None:
        self.last_expr = ""

    def eval(self, expr: str) -> str:
        self.last_expr = expr
        if expr == "2+3":
            return "5"
        if expr == "⍳5":
            return "1 2 3 4 5"
        return "42"

    def close(self) -> None:
        pass


@pytest.fixture
def app_with_pico():
    app = create_app()
    app["pico"] = FakePicoConnection()
    return app


async def test_ws_pico_eval(aiohttp_client, app_with_pico):
    client = await aiohttp_client(app_with_pico)
    ws = await client.ws_connect("/ws")
    # Switch to pico mode
    await ws.send_json({"type": "mode", "mode": "pico"})
    msg = await ws.receive_json()
    assert msg["type"] == "mode_changed"
    # Eval on pico
    await ws.send_json({"type": "eval", "expr": "2+3"})
    msg = await ws.receive_json()
    assert msg["type"] == "result"
    assert "5" in msg["html"]
    await ws.close()


async def test_ws_pico_then_local(aiohttp_client, app_with_pico):
    client = await aiohttp_client(app_with_pico)
    ws = await client.ws_connect("/ws")
    # Switch to pico
    await ws.send_json({"type": "mode", "mode": "pico"})
    await ws.receive_json()
    # Switch back to local
    await ws.send_json({"type": "mode", "mode": "local"})
    msg = await ws.receive_json()
    assert msg["type"] == "mode_changed"
    assert msg["mode"] == "local"
    # Eval locally
    await ws.send_json({"type": "eval", "expr": "2+3"})
    msg = await ws.receive_json()
    assert msg["type"] == "result"
    assert "5" in msg["html"]
    await ws.close()
