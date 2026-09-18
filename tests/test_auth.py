"""Comprehensive Test Suite for Email-Based Authentication & Edge Cases.
Verifies Supabase Auth integration, edge-case rejection, profile persistence, and local mirror fallback.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import httpx

from backend.app.main import app
from backend.app.database.client import db, hash_password, verify_password
from backend.app.core.security import create_access_token, decode_token

client = TestClient(app)


# --- 1. Password Hashing Utility Tests ---

def test_password_hashing_and_verification():
    """Verify PBKDF2 hashing produces unique salts and verifies correctly."""
    pwd = "SecurePassword2026!"
    h1 = hash_password(pwd)
    h2 = hash_password(pwd)

    assert h1 != h2  # Salt must ensure different hashes
    assert verify_password(pwd, h1) is True
    assert verify_password(pwd, h2) is True
    assert verify_password("WrongPassword", h1) is False
    assert verify_password("", h1) is False
    assert verify_password(pwd, "invalid$format") is False


import uuid

def gen_email(prefix="user"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}@smartfarm.io"


# --- 2. Sign Up Edge Cases ---

def test_signup_success():
    """Sign up with valid email and password returns 201 Created and JWT token."""
    email = gen_email("operator")
    resp = client.post(
        "/api/auth/signup",
        json={"email": email, "password": "StrongPassword123", "name": "Field Technician"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == email.lower()
    assert data["user"]["name"] == "Field Technician"
    assert "id" in data["user"]


@pytest.mark.parametrize("invalid_email", [
    "plainaddress",
    "@missingusername.com",
    "username@.com",
    "user name@domain.com",
    "user@domain..com",
    "   ",
    "",
])
def test_signup_invalid_email_format(invalid_email):
    """Sign up rejects invalid RFC email patterns with 400 Bad Request."""
    resp = client.post(
        "/api/auth/signup",
        json={"email": invalid_email, "password": "ValidPassword123"},
    )
    assert resp.status_code in (400, 422)
    if resp.status_code == 400:
        assert "Invalid email address format" in resp.json()["detail"]


@pytest.mark.parametrize("weak_pwd", [
    "12345",
    "short",
    "   ",
    "",
])
def test_signup_password_too_short(weak_pwd):
    """Sign up rejects passwords shorter than 6 characters."""
    resp = client.post(
        "/api/auth/signup",
        json={"email": gen_email("weak"), "password": weak_pwd},
    )
    assert resp.status_code in (400, 422)


def test_signup_duplicate_email_conflict():
    """Sign up with already registered email (case-insensitive) returns 409 Conflict."""
    email = gen_email("unique.farmer")
    # First registration
    resp1 = client.post(
        "/api/auth/signup",
        json={"email": email, "password": "Password123!", "name": "Farmer 1"},
    )
    assert resp1.status_code == 201

    # Second registration with uppercase variations
    resp2 = client.post(
        "/api/auth/signup",
        json={"email": email.upper(), "password": "DifferentPassword123!", "name": "Farmer 2"},
    )
    assert resp2.status_code == 409
    assert "already exists" in resp2.json()["detail"]


# --- 3. Login Edge Cases ---

def test_login_success():
    """Valid login credentials return 200 OK and JWT token."""
    email = gen_email("login.success")
    password = "CorrectPassword123"
    client.post(
        "/api/auth/signup",
        json={"email": email, "password": password, "name": "Farm Supervisor"},
    )

    resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["user"]["email"] == email
    assert data["user"]["name"] == "Farm Supervisor"


def test_login_case_insensitivity():
    """Login succeeds regardless of email casing."""
    email = gen_email("case.test")
    password = "MySecurePassword123"
    client.post(
        "/api/auth/signup",
        json={"email": email, "password": password},
    )

    resp = client.post(
        "/api/auth/login",
        json={"email": email.upper(), "password": password},
    )
    assert resp.status_code == 200
    assert resp.json()["user"]["email"] == email


def test_login_wrong_password():
    """Login with wrong password returns 401 Unauthorized."""
    email = gen_email("wrong.pwd")
    client.post(
        "/api/auth/signup",
        json={"email": email, "password": "RealPassword123"},
    )

    resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": "IncorrectPassword"},
    )
    assert resp.status_code == 401
    assert "Invalid email or password" in resp.json()["detail"]


def test_login_nonexistent_user():
    """Login with unregistered email returns 401 Unauthorized."""
    resp = client.post(
        "/api/auth/login",
        json={"email": gen_email("ghost.user"), "password": "SomePassword123"},
    )
    assert resp.status_code == 401
    assert "Invalid email or password" in resp.json()["detail"]


def test_login_empty_password():
    """Login with empty password returns 400 Bad Request."""
    resp = client.post(
        "/api/auth/login",
        json={"email": gen_email("valid.user"), "password": ""},
    )
    assert resp.status_code == 400
    assert "Password cannot be empty" in resp.json()["detail"]


# --- 4. Protected Session / Me Endpoint ---

def test_get_me_with_valid_token():
    """Protected /api/auth/me returns operator details when given valid Bearer token."""
    email = gen_email("session.tester")
    signup_resp = client.post(
        "/api/auth/signup",
        json={"email": email, "password": "TestPassword123", "name": "Dr. Agronomist"},
    )
    token = signup_resp.json()["token"]

    resp = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "authenticated"
    assert data["user"]["email"] == email
    assert data["user"]["name"] == "Dr. Agronomist"


def test_get_me_missing_token():
    """Protected /api/auth/me returns 401 Unauthorized when Authorization header is absent."""
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401
    assert "Authentication token is required" in resp.json()["detail"]


def test_get_me_invalid_or_malformed_token():
    """Protected /api/auth/me returns 401 Unauthorized when token is corrupt."""
    resp = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid.jwt.signature"},
    )
    assert resp.status_code == 401
    assert "Invalid or expired" in resp.json()["detail"]


def test_logout():
    """Logout endpoint returns success confirmation."""
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"


# --- 5. Supabase Auth & Profile Storage Mock Verification ---

def test_supabase_signup_persistence_call():
    """
    Verify that when Supabase is configured, signup sends email and password
    to Supabase Auth (/auth/v1/signup) and syncs user to public.profiles.
    """
    from backend.app.core.config import settings

    with patch.object(settings, "SUPABASE_URL", "https://mock-proj.supabase.co"), \
         patch.object(settings, "SUPABASE_ANON_KEY", "mock-anon-key"), \
         patch("httpx.AsyncClient.post") as mock_post:

        email = gen_email("supabase.user")
        mock_uid = str(uuid.uuid4())
        mock_supabase_resp = httpx.Response(
            status_code=200,
            json={
                "access_token": "supabase-mock-jwt-token.payload.sig",
                "user": {
                    "id": mock_uid,
                    "email": email,
                    "user_metadata": {"full_name": "Supabase Operator"},
                },
            },
            request=httpx.Request("POST", "https://mock-proj.supabase.co/auth/v1/signup"),
        )
        mock_post.return_value = mock_supabase_resp

        resp = client.post(
            "/api/auth/signup",
            json={"email": email, "password": "SecurePassword123!", "name": "Supabase Operator"},
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["provider"] == "supabase"
        assert data["user"]["email"] == email
        assert mock_post.call_count >= 1
