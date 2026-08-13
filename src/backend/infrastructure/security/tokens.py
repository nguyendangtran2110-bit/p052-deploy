from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any
from uuid import uuid4

import jwt
from jwt import PyJWTError

from src.backend.core.config import Settings
from src.backend.domain.common.errors import AuthenticationError
from src.backend.domain.identity.enums import ActorRole, ManagementRole, TokenType


@dataclass(frozen=True, slots=True)
class TokenEnvelope:
    token: str
    jti: str
    expires_at: datetime


class JwtTokenService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def create(
        self,
        *,
        subject: str,
        role: ActorRole,
        token_type: TokenType,
        token_version: int,
        resident_id: str | None = None,
        management_role: ManagementRole | None = None,
        session_id: str | None = None,
    ) -> TokenEnvelope:
        now = datetime.now(UTC)
        lifetime = (
            timedelta(minutes=self.settings.jwt_access_token_minutes)
            if token_type is TokenType.ACCESS
            else timedelta(days=self.settings.jwt_refresh_token_days)
        )
        expires_at = now + lifetime
        jti = str(uuid4())
        payload: dict[str, Any] = {
            "sub": subject,
            "role": role.value,
            "type": token_type.value,
            "ver": token_version,
            "jti": jti,
            "iss": self.settings.jwt_issuer,
            "aud": self.settings.jwt_audience,
            "iat": now,
            "nbf": now,
            "exp": expires_at,
        }
        if resident_id:
            payload["resident_id"] = resident_id
        if management_role:
            payload["management_role"] = management_role.value
        if session_id:
            payload["sid"] = session_id

        token = jwt.encode(payload, self.settings.jwt_secret_key, algorithm=self.settings.jwt_algorithm)
        return TokenEnvelope(token=token, jti=jti, expires_at=expires_at)

    def decode(self, token: str, expected_type: TokenType) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm],
                audience=self.settings.jwt_audience,
                issuer=self.settings.jwt_issuer,
                options={"require": ["sub", "role", "type", "ver", "jti", "iss", "aud", "iat", "nbf", "exp"]},
            )
        except PyJWTError as exc:
            raise AuthenticationError("Token is invalid or expired") from exc

        if payload.get("type") != expected_type.value:
            raise AuthenticationError("Token type is invalid")
        return payload


def hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()
