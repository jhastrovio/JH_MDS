from __future__ import annotations

import os

import aiohttp
import pyarrow as pa
import pyarrow.parquet as pq

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0/me/drive/root:/{path}:/content"
TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"


async def _get_access_token(session: aiohttp.ClientSession) -> str:
    data = {
        "client_id": os.environ.get("ONE_DRIVE_CLIENT_ID"),
        "client_secret": os.environ.get("ONE_DRIVE_CLIENT_SECRET"),
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
    }
    async with session.post(TOKEN_URL, data=data) as resp:
        resp.raise_for_status()
        payload = await resp.json()
        return payload["access_token"]


async def upload_bytes(path: str, data: bytes) -> None:
    async with aiohttp.ClientSession() as session:
        token = await _get_access_token(session)
        url = GRAPH_BASE_URL.format(path=path)
        headers = {"Authorization": f"Bearer {token}"}
        async with session.put(url, headers=headers, data=data) as resp:
            resp.raise_for_status()


def table_to_bytes(table: pa.Table) -> bytes:
    sink = pa.BufferOutputStream()
    pq.write_table(table, sink)
    return sink.getvalue().to_pybytes()


async def upload_table(table: pa.Table, path: str) -> None:
    data = table_to_bytes(table)
    await upload_bytes(path, data)
