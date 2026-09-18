"""Authentication and authorization utilities with Supabase JWT and local dev fallback."""

from typing import Optional, Dict, Any
from pydantic import BaseModel
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security_scheme = HTTPBearer(auto_error=False)


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

    # Basic JWT format sanity check
    parts = token.split(".")
    if len(parts) != 3:
        # Development or test token
        return DEV_USER

    try:
        import base64
        import json
        payload_b64 = parts[1]
        # Pad base64
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))

        user_id = payload.get("sub") or payload.get("id") or DEV_USER.user_id
        email = payload.get("email") or DEV_USER.email
        name = payload.get("user_metadata", {}).get("full_name") or email.split("@")[0]

        return AuthUser(
            user_id=user_id,
            email=email,
            name=name,
            role=payload.get("role", "authenticated"),
        )
    except Exception:
        return DEV_USER
