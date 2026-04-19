"""Tests for WebSocket communication."""

import pytest

pytestmark = pytest.mark.slow

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


async def test_ws_save_and_list_sessions(aiohttp_client, app, tmp_path):
    app["sessions_dir"] = str(tmp_path)
    client = await aiohttp_client(app)
    ws = await client.ws_connect("/ws")
    # Eval something to have a transcript
    await ws.send_json({"type": "eval", "expr": "2+3"})
    await ws.receive_json()  # result
    await ws.receive_json()  # workspace
    # Save
    await ws.send_json({"type": "save_session", "name": "test1"})
    msg = await ws.receive_json()
    assert msg["type"] == "session_saved"
    assert msg["name"] == "test1"
    # List
    await ws.send_json({"type": "list_sessions"})
    msg = await ws.receive_json()
    assert msg["type"] == "session_list"
    assert "test1" in msg["sessions"]
    await ws.close()


async def test_ws_load_session(aiohttp_client, app, tmp_path):
    app["sessions_dir"] = str(tmp_path)
    client = await aiohttp_client(app)
    ws = await client.ws_connect("/ws")
    # Eval and save
    await ws.send_json({"type": "eval", "expr": "x←42"})
    await ws.receive_json()  # result
    await ws.receive_json()  # workspace
    await ws.send_json({"type": "eval", "expr": "x+1"})
    await ws.receive_json()  # result
    await ws.receive_json()  # workspace
    await ws.send_json({"type": "save_session", "name": "test2"})
    await ws.receive_json()  # saved
    # Clear and load
    await ws.send_json({"type": "system", "cmd": ")clear"})
    await ws.receive_json()  # result
    await ws.receive_json()  # workspace
    await ws.send_json({"type": "load_session", "name": "test2"})
    msg = await ws.receive_json()
    assert msg["type"] == "session_loaded"
    assert "42" in msg["html"] or "43" in msg["html"]
    await ws.close()


async def test_ws_check_session_exists(aiohttp_client, app, tmp_path):
    app["sessions_dir"] = str(tmp_path)
    client = await aiohttp_client(app)
    ws = await client.ws_connect("/ws")
    # Save a session
    await ws.send_json({"type": "eval", "expr": "1+1"})
    await ws.receive_json()  # result
    await ws.receive_json()  # workspace
    await ws.send_json({"type": "save_session", "name": "existing"})
    await ws.receive_json()  # saved
    # Check it exists
    await ws.send_json({"type": "check_session", "name": "existing"})
    msg = await ws.receive_json()
    assert msg["type"] == "session_exists"
    assert msg["exists"] is True
    # Check one that doesn't
    await ws.send_json({"type": "check_session", "name": "nope"})
    msg = await ws.receive_json()
    assert msg["type"] == "session_exists"
    assert msg["exists"] is False
    await ws.close()


async def test_ws_delete_session(aiohttp_client, app, tmp_path):
    app["sessions_dir"] = str(tmp_path)
    client = await aiohttp_client(app)
    ws = await client.ws_connect("/ws")
    # Save a session
    await ws.send_json({"type": "eval", "expr": "1+1"})
    await ws.receive_json()
    await ws.receive_json()
    await ws.send_json({"type": "save_session", "name": "deleteme"})
    await ws.receive_json()
    # Delete it
    await ws.send_json({"type": "delete_session", "name": "deleteme"})
    msg = await ws.receive_json()
    assert msg["type"] == "session_deleted"
    assert msg["name"] == "deleteme"
    # Verify it's gone
    await ws.send_json({"type": "list_sessions"})
    msg = await ws.receive_json()
    assert "deleteme" not in msg["sessions"]
    await ws.close()


async def test_ws_delete_nonexistent(aiohttp_client, app, tmp_path):
    app["sessions_dir"] = str(tmp_path)
    client = await aiohttp_client(app)
    ws = await client.ws_connect("/ws")
    await ws.send_json({"type": "delete_session", "name": "ghost"})
    msg = await ws.receive_json()
    assert msg["type"] == "error"
    await ws.close()


