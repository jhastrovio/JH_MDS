import json
import os
import sys
import asyncio
from pathlib import Path

import pytest
import websockets

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import ingest.saxo_ws as saxo_ws  # noqa: E402


class DummyRedis:
    def __init__(self):
        self.data = {}
        self.closed = False

    async def set(self, key: str, value: str, ex: int | None = None):
        self.data[key] = value

    async def close(self):
        self.closed = True


class DummyWS:
    def __init__(self, messages, error=None):
        self.messages = list(messages)
        self.error = error

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def send(self, message):
        self.sent = message

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.messages:
            return self.messages.pop(0)
        if self.error:
            raise self.error
        raise asyncio.CancelledError


@pytest.mark.asyncio
async def test_reconnect_on_disconnect(monkeypatch: pytest.MonkeyPatch) -> None:
    tick1 = json.dumps({"Symbol": "EUR-USD", "Bid": 1.0, "Ask": 1.1, "TimeStamp": "t1"})
    tick2 = json.dumps({"Symbol": "EUR-USD", "Bid": 1.2, "Ask": 1.3, "TimeStamp": "t2"})

    ws1 = DummyWS([tick1], error=websockets.WebSocketException("boom"))
    ws2 = DummyWS([tick2])
    connections = [ws1, ws2]
    count = 0

    async def fake_connect():
        nonlocal count
        ws = connections[count]
        count += 1
        return ws

    monkeypatch.setattr(saxo_ws, "_connect", fake_connect)
    os.environ.setdefault("SAXO_API_TOKEN", "token")

    redis = DummyRedis()

    await saxo_ws.stream_quotes(["EUR-USD"], redis)

    assert count == 2
    assert redis.closed
    assert json.loads(redis.data["fx:EUR-USD"]) == {
        "symbol": "EUR-USD",
        "bid": 1.2,
        "ask": 1.3,
        "timestamp": "t2",
    }
