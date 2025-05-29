import os
import sys
import time
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from importlib import import_module  # noqa: E402

router_module = import_module("app.auth.router")
_verify_jwt = router_module._verify_jwt  # type: ignore[attr-defined]
HTTPAuthorizationCredentials = router_module.HTTPAuthorizationCredentials

from jose import jwt  # noqa: E402


def make_credentials(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_invalid_token_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    os.environ.setdefault("JWT_SECRET", "secret")
    token = jwt.encode({"exp": time.time() + 60}, "wrong", algorithm="HS256")
    creds = make_credentials(token)
    with pytest.raises(router_module.HTTPException) as exc:
        _verify_jwt(creds)
    assert exc.value.status_code == 401


def test_expired_token_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    os.environ.setdefault("JWT_SECRET", "secret")
    token = jwt.encode({"exp": time.time() - 10}, "secret", algorithm="HS256")
    creds = make_credentials(token)
    with pytest.raises(router_module.HTTPException) as exc:
        _verify_jwt(creds)
    assert exc.value.status_code == 401
