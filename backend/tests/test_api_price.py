import json
import os
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from importlib import import_module  # noqa: E402

router_module = import_module("app.auth.router")
get_price = router_module.get_price  # type: ignore[attr-defined]


class DummyRedis:
    def __init__(self, store: dict[str, str]):
        self._store = store

    async def get(self, key: str):
        return self._store.get(key)

    async def close(self):
        pass


@pytest.mark.asyncio
async def test_get_price(monkeypatch: pytest.MonkeyPatch) -> None:
    data = json.dumps(
        {
            "symbol": "EUR-USD",
            "bid": 1.0,
            "ask": 1.1,
            "timestamp": "2025-05-22T08:15:30Z",
        }
    )
    dummy = DummyRedis({"fx:EUR-USD": data})
    monkeypatch.setattr(router_module, "get_redis", lambda: dummy)
    monkeypatch.setattr(router_module, "_verify_jwt", lambda credentials=None: None)
    os.environ.setdefault("JWT_SECRET", "secret")

    price = await get_price("EUR-USD")

    assert price.symbol == "EUR-USD"
    assert abs(price.price - 1.05) < 1e-6
    assert price.timestamp == "2025-05-22T08:15:30Z"
