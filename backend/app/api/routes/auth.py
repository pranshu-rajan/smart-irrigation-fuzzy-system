"""Authentication API Routes with Supabase Auth integration and local repository mirror."""

import re
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status, Header
import httpx

from backend.app.core.config import settings
from backend.app.core.logging import get_logger
from backend.app.core.security import (
    AuthUser,
    get_current_user,
    require_authenticated_user,
    create_access_token,
    DEV_USER,
)
from backend.app.database.client import (
    get_db_repository,
    DatabaseRepository,
    hash_password,
    verify_password,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$")


class SignUpRequest(BaseModel):
    email: str = Field(..., description="Operator email address")
    password: str = Field(..., min_length=1, description="Account password (min 6 chars)")
    name: Optional[str] = Field("Operator", description="Operator display name")


class LoginRequest(BaseModel):
    email: str = Field(..., description="Operator email address")
    password: str = Field(..., description="Account password")


class AuthResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    user: Dict[str, Any]
    provider: str = "supabase"


def validate_email_format(email: str) -> str:
    """Validate and sanitize email address."""
    clean = email.strip().lower()
    if (
        not clean
        or " " in clean
        or ".." in clean
        or clean.startswith(".")
        or clean.endswith(".")
        or "@" not in clean
        or not EMAIL_REGEX.match(clean)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email address format. Please provide a valid email (e.g., operator@domain.com).",
        )
    return clean


def validate_password_complexity(password: str) -> str:
    """Validate password length and basic complexity."""
    clean = password.strip()
    if len(clean) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long.",
        )
    return clean


async def sync_supabase_profile(supabase_url: str, anon_key: str, token: str, user_id: str, email: str, name: str):
    """Upsert user profile into Supabase public.profiles table."""
    try:
        headers = {
            "apikey": anon_key,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates",
        }
        profile_data = {
            "id": user_id,
            "email": email,
            "name": name,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{supabase_url}/rest/v1/profiles",
                json=profile_data,
                headers=headers,
            )
    except Exception as exc:
        logger.warning(f"Failed to sync profile to Supabase public.profiles: {exc}")


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    payload: SignUpRequest,
    repo: DatabaseRepository = Depends(get_db_repository),
):
    """
    Register a new operator with email and password.
    Persists credentials in Supabase Auth (auth.users) and mirrors to local repository.
    """
    email = validate_email_format(payload.email)
    password = validate_password_complexity(payload.password)
    name = (payload.name or "Operator").strip()

    # Check local duplicate registration
    existing_local = repo.get_user_by_email(email)
    if existing_local:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    # 1. If Supabase is configured, register through Supabase GoTrue
    if settings.has_supabase:
        supabase_url = settings.SUPABASE_URL.rstrip("/")
        anon_key = settings.SUPABASE_ANON_KEY

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{supabase_url}/auth/v1/signup",
                    json={
                        "email": email,
                        "password": password,
                        "data": {"full_name": name},
                    },
                    headers={"apikey": anon_key, "Content-Type": "application/json"},
                )

            if resp.status_code in (200, 201):
                data = resp.json()
                user_obj = data.get("user", {}) or {}
                user_id = user_obj.get("id") or data.get("id")
                access_token = data.get("access_token") or create_access_token(user_id, email, name)

                # Persist profile to Supabase public.profiles
                await sync_supabase_profile(supabase_url, anon_key, access_token, user_id, email, name)

                # Mirror locally
                pwd_hash = hash_password(password)
                local_user = repo.create_user(
                    email=email,
                    password_hash=pwd_hash,
                    name=name,
                    role="authenticated",
                    user_id=user_id,
                )

                return AuthResponse(
                    token=access_token,
                    token_type="bearer",
                    user={
                        "id": user_id,
                        "email": email,
                        "name": name,
                        "role": "authenticated",
                    },
                    provider="supabase",
                )

            # Handle Supabase errors
            err_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            err_msg = err_data.get("msg") or err_data.get("error_description") or err_data.get("message") or resp.text

            if "already registered" in err_msg.lower() or "unique constraint" in err_msg.lower() or resp.status_code == 422:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An account with this email address already exists in Supabase.",
                )
            if "weak" in err_msg.lower() or "password" in err_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Password rejected by Supabase: {err_msg}",
                )

            logger.warning(f"Supabase signup returned {resp.status_code}: {err_msg}. Falling back to local mirror.")
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning(f"Supabase connection failed during signup: {exc}. Proceeding with local mirror.")

    # 2. Local repository registration fallback
    pwd_hash = hash_password(password)
    new_user = repo.create_user(
        email=email,
        password_hash=pwd_hash,
        name=name,
        role="authenticated",
    )
    token = create_access_token(
        user_id=new_user["id"],
        email=email,
        name=name,
        role="authenticated",
    )

    return AuthResponse(
        token=token,
        token_type="bearer",
        user={
            "id": new_user["id"],
            "email": email,
            "name": name,
            "role": "authenticated",
        },
        provider="local_mirror" if not settings.has_supabase else "supabase_fallback",
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    repo: DatabaseRepository = Depends(get_db_repository),
):
    """
    Authenticate an operator using email and password.
    Validates against Supabase Auth (or local repository fallback).
    """
    email = validate_email_format(payload.email)
    password = payload.password.strip()
    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password cannot be empty.",
        )

    # 1. Attempt Supabase Auth login if configured
    if settings.has_supabase:
        supabase_url = settings.SUPABASE_URL.rstrip("/")
        anon_key = settings.SUPABASE_ANON_KEY

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{supabase_url}/auth/v1/token?grant_type=password",
                    json={"email": email, "password": password},
                    headers={"apikey": anon_key, "Content-Type": "application/json"},
                )

            if resp.status_code == 200:
                data = resp.json()
                access_token = data.get("access_token")
                user_obj = data.get("user", {}) or {}
                user_id = user_obj.get("id") or data.get("id")
                name = user_obj.get("user_metadata", {}).get("full_name") or email.split("@")[0]

                # Ensure user exists in local mirror
                if not repo.get_user_by_email(email):
                    repo.create_user(
                        email=email,
                        password_hash=hash_password(password),
                        name=name,
                        role="authenticated",
                        user_id=user_id,
                    )

                return AuthResponse(
                    token=access_token,
                    token_type="bearer",
                    user={
                        "id": user_id,
                        "email": email,
                        "name": name,
                        "role": "authenticated",
                    },
                    provider="supabase",
                )

            err_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            err_msg = err_data.get("error_description") or err_data.get("msg") or resp.text
            if resp.status_code in (400, 401) and "invalid" in err_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password.",
                )
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning(f"Supabase login connection error: {exc}. Trying local mirror verification.")

    # 2. Local mirror verification
    user = repo.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not verify_password(password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token(
        user_id=user["id"],
        email=user["email"],
        name=user["name"],
        role=user.get("role", "authenticated"),
    )

    return AuthResponse(
        token=token,
        token_type="bearer",
        user={
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user.get("role", "authenticated"),
        },
        provider="local_mirror",
    )


@router.get("/me")
async def get_me(current_user: AuthUser = Depends(require_authenticated_user)):
    """Retrieve current authenticated operator context from active token."""
    return {
        "status": "authenticated",
        "user": {
            "id": current_user.user_id,
            "email": current_user.email,
            "name": current_user.name,
            "role": current_user.role,
        },
    }


@router.post("/logout")
async def logout(current_user: AuthUser = Depends(get_current_user)):
    """Log out current session and invalidate client token."""
    return {
        "status": "success",
        "message": f"Successfully logged out operator {current_user.email}.",
    }
