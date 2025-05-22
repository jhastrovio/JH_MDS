import os


def test_import_modules() -> None:
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
    import ingest.saxo_ws as saxo_ws
    import storage.on_drive as on_drive
    import storage.redis_client as redis_client

    assert callable(redis_client.get_redis)
    assert hasattr(saxo_ws, "stream_quotes")
    assert hasattr(on_drive, "upload_bytes")
