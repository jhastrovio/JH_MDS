import json
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import ingest.saxo_ws as saxo_ws  # noqa: E402


class DummyWebSocket:
    def __init__(self, messages: list[str]):
        self._messages = messages
        self.sent = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def send(self, message: str):
        self.sent.append(message)

    def __aiter__(self):
        self._iter = iter(self._messages)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration


class DummyRedis:
    def __init__(self):
        self.set_store: dict[str, str] = {}
        self.lists: dict[str, list[str]] = {}
        self.expiry: dict[str, int] = {}

    async def set(self, key: str, value: str, ex: int | None = None):
        self.set_store[key] = value

    async def lpush(self, key: str, value: str):
        self.lists.setdefault(key, []).insert(0, value)

    async def ltrim(self, key: str, start: int, end: int):
        lst = self.lists.get(key, [])
        self.lists[key] = lst[start : end + 1]

    async def expire(self, key: str, ex: int):
        self.expiry[key] = ex

    async def close(self):
        pass


@pytest.mark.asyncio
async def test_stream_quotes_populates_tick_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    messages = [
        json.dumps(
            {
                "Symbol": "EUR-USD",
                "Bid": i,
                "Ask": i + 0.1,
                "TimeStamp": f"2025-05-22T08:{i:02d}:00Z",
            }
        )
        for i in range(saxo_ws.MAX_TICKS_PER_SYMBOL + 5)
    ]
    ws = DummyWebSocket(messages)

    async def dummy_connect():
        return ws

    monkeypatch.setattr(saxo_ws, "_connect", dummy_connect)
    redis = DummyRedis()

    await saxo_ws.stream_quotes(["EUR-USD"], redis)

    key = "ticks:EUR-USD"
    assert len(redis.lists[key]) == saxo_ws.MAX_TICKS_PER_SYMBOL
    # newest tick should be first due to LPUSH
    assert json.loads(redis.lists[key][0])["bid"] == saxo_ws.MAX_TICKS_PER_SYMBOL + 4
    # oldest retained tick should correspond to index 5 (trimmed first 5)
    assert json.loads(redis.lists[key][-1])["bid"] == 5
