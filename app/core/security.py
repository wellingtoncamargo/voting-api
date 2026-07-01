from __future__ import annotations

import base64
import hashlib
import hmac
import json
import binascii
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.domain.exceptions.exceptions import AutenticacaoInvalidaError


def _b64url_encode(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")


def gerar_token_bearer(cpf: str, role: str) -> str:
    agora = datetime.now(timezone.utc)
    expira_em = agora + timedelta(minutes=settings.AUTH_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": cpf,
        "role": role,
        "iat": int(agora.timestamp()),
        "exp": int(expira_em.timestamp()),
    }
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    assinatura = hmac.new(
        settings.AUTH_SECRET_KEY.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).digest()
    return f"{_b64url_encode(payload_bytes)}.{_b64url_encode(assinatura)}"


def decodificar_token_bearer(token: str) -> dict:
    try:
        payload_b64, signature_b64 = token.split(".", 1)
        payload_bytes = _b64url_decode(payload_b64)
        signature = _b64url_decode(signature_b64)
    except (ValueError, binascii.Error) as exc:
        raise AutenticacaoInvalidaError("Token bearer inválido.") from exc

    expected_signature = hmac.new(
        settings.AUTH_SECRET_KEY.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).digest()

    if not hmac.compare_digest(signature, expected_signature):
        raise AutenticacaoInvalidaError("Assinatura do token inválida.")

    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise AutenticacaoInvalidaError("Token bearer inválido.") from exc

    exp = payload.get("exp")
    if not isinstance(exp, int):
        raise AutenticacaoInvalidaError("Token bearer sem expiração válida.")

    agora = int(datetime.now(timezone.utc).timestamp())
    if exp < agora:
        raise AutenticacaoInvalidaError("Token bearer expirado.")

    return payload
