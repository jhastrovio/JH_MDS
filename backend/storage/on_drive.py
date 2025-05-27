"""Helpers for persisting data to Microsoft OneDrive via Graph API.

The functions in this module handle authentication using OAuth client
credentials and provide utilities to upload bytes or Arrow tables as Parquet
files. They are designed for asynchronous, serverless use.
"""

from __future__ import annotations

import os

import aiohttp
import pyarrow as pa
import pyarrow.parquet as pq

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0/me/drive/root:/{path}:/content"
TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"


async def _get_access_token(session: aiohttp.ClientSession) -> str:
    """Fetch an OAuth access token for the Microsoft Graph API.

    Parameters
    ----------
    session : aiohttp.ClientSession
        HTTP session used to perform the token request.

    Returns
    -------
    str
        The access token string to include in subsequent requests.
    """

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
    """Upload raw bytes to OneDrive at the given path.

    Parameters
    ----------
    path : str
        The target file path relative to the user's OneDrive root.
    data : bytes
        The binary payload to upload.
    """

    async with aiohttp.ClientSession() as session:
        token = await _get_access_token(session)
        url = GRAPH_BASE_URL.format(path=path)
        headers = {"Authorization": f"Bearer {token}"}
        async with session.put(url, headers=headers, data=data) as resp:
            resp.raise_for_status()


def table_to_bytes(table: pa.Table) -> bytes:
    """Serialize an Arrow table to Parquet bytes in memory.

    Parameters
    ----------
    table : pa.Table
        The Arrow table to serialize.

    Returns
    -------
    bytes
        The Parquet-encoded representation of ``table``.
    """

    sink = pa.BufferOutputStream()
    pq.write_table(table, sink)
    return sink.getvalue().to_pybytes()


async def upload_table(table: pa.Table, path: str) -> None:
    """Upload an Arrow table to OneDrive as a Parquet file.

    Parameters
    ----------
    table : pa.Table
        The table to persist.
    path : str
        Destination path for the uploaded file relative to the OneDrive root.
    """

    data = table_to_bytes(table)
    await upload_bytes(path, data)
