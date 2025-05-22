import os
import sys
from pathlib import Path


# Ensure repository root is on ``sys.path`` when tests are invoked from the
# ``tests`` directory. Pytest adds the tests directory to ``sys.path`` by
# default, so direct imports like ``ingest`` would fail without this tweak.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def test_import_modules() -> None:
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
    import ingest.saxo_ws as saxo_ws
    import storage.on_drive as on_drive
    import storage.redis_client as redis_client

    assert callable(redis_client.get_redis)
    assert hasattr(saxo_ws, "stream_quotes")
    assert hasattr(on_drive, "upload_bytes")
