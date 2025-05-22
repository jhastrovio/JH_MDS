from __future__ import annotations

import base64
import json
import time
import hmac
import hashlib

from .exceptions import JWTError


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def encode(claims: dict[str, object], key: str, algorithm: str = "HS256") -> str:
    if algorithm != "HS256":
        raise JWTError("Unsupported algorithm")
    header = {"alg": algorithm, "typ": "JWT"}
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64url_encode(json.dumps(claims, separators=(",", ":")).encode())
    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(key.encode(), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode(
    token: str, key: str, algorithms: list[str] | str, options: dict | None = None
) -> dict:
    if isinstance(algorithms, str):
        algorithms = [algorithms]
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
    except ValueError as exc:
        raise JWTError("Malformed token") from exc
    header = json.loads(_b64url_decode(header_b64))
    if header.get("alg") not in algorithms:
        raise JWTError("Invalid algorithm")
    signing_input = f"{header_b64}.{payload_b64}".encode()
    expected = hmac.new(key.encode(), signing_input, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, _b64url_decode(sig_b64)):
        raise JWTError("Invalid signature")
    payload = json.loads(_b64url_decode(payload_b64))
    if payload.get("exp") is not None and time.time() > payload["exp"]:
        raise JWTError("Signature has expired")
    return payload
