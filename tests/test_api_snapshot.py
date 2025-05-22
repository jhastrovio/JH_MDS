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
create_snapshot = router_module.create_snapshot  # type: ignore[attr-defined]


class DummyRedis:
    def __init__(self, store: dict[str, str]):
        self._store = store

    async def get(self, key: str):
        return self._store.get(key)

    async def close(self):
        pass


class DummyUploader:
    def __init__(self):
        self.called = False
        self.table = None
        self.path = None

    async def __call__(self, table, path):
        self.called = True
        self.table = table
        self.path = path


@pytest.mark.asyncio
async def test_create_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    tick = json.dumps(
        {
            "symbol": "EUR-USD",
            "bid": 1.0,
            "ask": 1.1,
            "timestamp": "2025-05-22T08:15:00Z",
        }
    )
    dummy_redis = DummyRedis({"fx:EUR-USD": tick})
    monkeypatch.setattr(router_module, "get_redis", lambda: dummy_redis)
    monkeypatch.setattr(router_module, "_verify_jwt", lambda credentials=None: None)
    uploader = DummyUploader()
    monkeypatch.setattr(router_module, "upload_table", uploader)
    os.environ.setdefault("JWT_SECRET", "secret")

    resp = await create_snapshot({"symbols": ["EUR-USD"]})

    assert uploader.called
    assert "snapshots/" in uploader.path
    assert resp["detail"] == "snapshot scheduled"
