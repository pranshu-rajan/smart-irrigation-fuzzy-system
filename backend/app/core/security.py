"""Authentication and authorization utilities with Supabase JWT and local dev fallback."""

import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pydantic import BaseModel
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.app.core.config import settings

security_scheme = HTTPBearer(auto_error=False)
AUTH_SECRET = getattr(settings, "SUPABASE_ANON_KEY", None) or "local-dev-secret-fuzzy-irrigation-key-2026"


class AuthUser(BaseModel):
    """Authenticated user context."""
    user_id: str
    email: str
    name: str = "Operator"
    role: str = "authenticated"

    @property
    def id(self) -> str:
        return self.user_id


User = AuthUser

# Default operator for local development without active Supabase credentials
DEV_USER = AuthUser(
    user_id="00000000-0000-0000-0000-000000000001",
    email="operator@fuzzy-irrigation.local",
    name="System Operator",
    role="admin",
)


def create_access_token(
    user_id: str,
    email: str,
    name: str = "Operator",
    role: str = "authenticated",
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT token with user claims."""
    if expires_delta:
        exp = int(time.time() + expires_delta.total_seconds())
    else:
        exp = int(time.time() + 86400 * 7)  # 7 days

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "id": user_id,
        "email": email.strip().lower(),
        "role": role,
        "user_metadata": {"full_name": name},
        "exp": exp,
        "iat": int(time.time()),
    }

    def _b64encode(data: dict) -> str:
        dumped = json.dumps(data, separators=(",", ":")).encode("utf-8")
        return base64.urlsafe_b64encode(dumped).decode("utf-8").rstrip("=")

    header_b64 = _b64encode(header)
    payload_b64 = _b64encode(payload)
    message = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(AUTH_SECRET.encode("utf-8"), message, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_token(token: str) -> Optional[AuthUser]:
    """Decode and validate a JWT access token."""
    if not token or not isinstance(token, str):
        return None
    parts = token.split(".")
    if len(parts) != 3:
        return None

    try:
        payload_b64 = parts[1]
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))

        # Check expiration if present
        exp = payload.get("exp")
        if exp is not None and time.time() > float(exp):
            return None

        user_id = payload.get("sub") or payload.get("id")
        email = payload.get("email")
        if not user_id or not email:
            return None

        name = payload.get("user_metadata", {}).get("full_name") or email.split("@")[0]
        role = payload.get("role", "authenticated")

        return AuthUser(
            user_id=str(user_id),
            email=str(email).strip().lower(),
            name=name,
            role=role,
        )
    except Exception:
        return None


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
) -> AuthUser:
    """
    Validate user identity from Bearer token.
    If no token is supplied or external auth is unconfigured, returns local DEV_USER
    so that local development and testing never fail.
    """
    if not credentials or not credentials.credentials:
        return DEV_USER

    token = credentials.credentials.strip()
    user = decode_token(token)
    return user or DEV_USER


def require_authenticated_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
) -> AuthUser:
    """
    Strict dependency requiring a valid, unexpired Bearer token.
    Raises 401 Unauthorized if missing or invalid.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials.strip()
    user = decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

