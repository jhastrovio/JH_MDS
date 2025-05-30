# test_imports.py

import os
import sys
from pathlib import Path
from importlib import import_module

# Ensure repository root is on sys.path when tests run from tests/
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

def test_import_modules() -> None:
    # Provide a dummy Redis URL so get_redis() can initialize
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

    # Service modules
    import services.saxo_ws as saxo_ws
    import storage.on_drive as on_drive

    # DI factory for Redis
    from core.deps import get_redis

    # ASGI app entrypoint
    api_module = import_module("routers.api")

    # Assertions
    assert hasattr(get_redis, "__call__"), "get_redis should be callable"  # :contentReference[oaicite:0]{index=0}
    assert hasattr(saxo_ws, "stream_quotes"), "saxo_ws.stream_quotes must exist"
    assert hasattr(on_drive, "upload_bytes"), "on_drive.upload_bytes must exist"
    assert hasattr(api_module, "app"), "routers.api must export 'app'"
