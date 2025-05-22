from __future__ import annotations

from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api import router as api_router
from api.deps import get_redis


class FakeRedis:
    def __init__(self):
        self.data = {}

    async def hgetall(self, key):
        return self.data.get(key, {})

    async def lrange(self, key, start, end):
        return self.data.get(key, [])

    async def hset(self, key, mapping):
        self.data[key] = mapping

    async def lpush(self, key, value):
        self.data.setdefault(key, []).insert(0, value)


@asynccontextmanager
async def override_redis():
    yield FakeRedis()


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(api_router, prefix="/api")
    return app


@pytest.fixture
async def client():
    app = create_app()
    app.dependency_overrides[get_redis] = override_redis
    async with TestClient(app) as client:
        yield client


def test_price_not_found(client):
    resp = client.get("/api/price", params={"symbol": "EUR-USD"})
    assert resp.status_code == 404


def test_ticks_not_found(client):
    resp = client.get("/api/ticks", params={"symbol": "EUR-USD"})
    assert resp.status_code == 404


def test_snapshot(client):
    resp = client.post("/api/snapshot", json={"symbols": ["EUR-USD"]})
    assert resp.status_code == 202
