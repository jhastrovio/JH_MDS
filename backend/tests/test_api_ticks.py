import json
import os
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from importlib import import_module  # noqa: E402

router_module = import_module("api.router")
get_ticks = router_module.get_ticks  # type: ignore[attr-defined]


class DummyRedis:
    def __init__(self, store: dict[str, list[str]]):
        self._store = store

    async def lrange(self, key: str, start: int, end: int):
        return self._store.get(key, [])

    async def close(self):
        pass


@pytest.mark.asyncio
async def test_get_ticks(monkeypatch: pytest.MonkeyPatch) -> None:
    ticks = [
        json.dumps(
            {
                "symbol": "EUR-USD",
                "bid": 1.0,
                "ask": 1.1,
                "timestamp": "2025-05-22T08:15:00Z",
            }
        ),
        json.dumps(
            {
                "symbol": "EUR-USD",
                "bid": 1.2,
                "ask": 1.3,
                "timestamp": "2025-05-22T08:16:00Z",
            }
        ),
    ]
    dummy = DummyRedis({"ticks:EUR-USD": ticks})
    monkeypatch.setattr(router_module, "get_redis", lambda: dummy)
    monkeypatch.setattr(router_module, "_verify_jwt", lambda credentials=None: None)
    os.environ.setdefault("JWT_SECRET", "secret")

    result = await get_ticks("EUR-USD")

    assert len(result) == 2
    assert result[0].bid == 1.0
    assert result[1].ask == 1.3

    result_since = await get_ticks("EUR-USD", since="2025-05-22T08:15:30Z")
    assert len(result_since) == 1
    assert result_since[0].bid == 1.2
