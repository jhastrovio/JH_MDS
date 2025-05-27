# ruff: noqa: E402
import sys
from pathlib import Path

# Ensure project root on ``sys.path`` as in ``test_imports``
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from storage.on_drive import (
    GRAPH_BASE_URL,
    table_to_bytes,
    upload_bytes,
    upload_table,
)


def test_table_to_bytes_round_trip() -> None:
    table = pa.table({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    data = table_to_bytes(table)
    assert isinstance(data, bytes)

    buffer = pa.BufferReader(data)
    restored = pq.read_table(buffer)
    assert restored.equals(table)


class MockResponse:
    def __init__(self, *, status: int = 200, json_data: dict | None = None):
        self.status = status
        self._json_data = json_data or {}
        self.data = b""
        self.headers: dict | None = None
        self.url: str | None = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status >= 400:
            raise RuntimeError(f"HTTP {self.status}")


class MockSession:
    def __init__(self):
        self.post_called = False
        self.put_called = False
        self.put_url = None
        self.put_headers = None
        self.put_data = None
        self.token_response = MockResponse(json_data={"access_token": "token"})
        self.put_response = MockResponse()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def post(self, url, data=None):
        self.post_called = True
        return self.token_response

    def put(self, url, headers=None, data=None):
        self.put_called = True
        self.put_url = url
        self.put_headers = headers
        self.put_data = data
        return self.put_response


class DummyClientSession:
    def __init__(self, *_, **__):
        self.session = MockSession()

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        pass


@pytest.mark.asyncio
async def test_upload_bytes(monkeypatch):
    dummy = DummyClientSession()
    monkeypatch.setattr("aiohttp.ClientSession", lambda: dummy)

    path = "folder/file.bin"
    data = b"abc"
    await upload_bytes(path, data)

    session = dummy.session
    assert session.post_called
    assert session.put_called
    assert session.put_url == GRAPH_BASE_URL.format(path=path)
    assert session.put_headers == {"Authorization": "Bearer token"}
    assert session.put_data == data


@pytest.mark.asyncio
async def test_upload_table(monkeypatch):
    dummy = DummyClientSession()
    monkeypatch.setattr("aiohttp.ClientSession", lambda: dummy)

    table = pa.table({"n": [1, 2]})
    expected = table_to_bytes(table)
    path = "snapshots/test.parquet"
    await upload_table(table, path)

    session = dummy.session
    assert session.post_called
    assert session.put_called
    assert session.put_data == expected
    assert session.put_url == GRAPH_BASE_URL.format(path=path)
