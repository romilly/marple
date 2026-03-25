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
