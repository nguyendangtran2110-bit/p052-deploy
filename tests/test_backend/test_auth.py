import jwt
import pytest

from src.backend.infrastructure.email import EmailService


def bootstrap_payload() -> dict:
    return {
        "email": "security-admin@example.com",
        "password": "SecureAdminPassword123!",
        "employee_code": "SEC-001",
        "full_name": "Security Administrator",
        "department": "Operations",
    }


@pytest.mark.asyncio
async def test_bootstrap_creates_real_management_jwt_and_login(client):
    created = await client.post(
        "/api/v1/auth/bootstrap-management",
        headers={"X-Bootstrap-Token": "test-management-bootstrap-token"},
        json=bootstrap_payload(),
    )

    assert created.status_code == 201
    data = created.json()
    claims = jwt.decode(
        data["access_token"],
        "test-jwt-secret-key-with-more-than-32-characters",
        algorithms=["HS256"],
        audience="onbxrd-test-clients",
        issuer="onbxrd-test-api",
    )
    assert claims["type"] == "access"
    assert claims["role"] == "management"
    assert claims["management_role"] == "admin"
    assert data["account"]["management_profile"]["employee_code"] == "SEC-001"

    bearer_headers = {"Authorization": f"Bearer {data['access_token']}"}
    me = await client.get("/api/v1/auth/me", headers=bearer_headers)
    logged_in = await client.post(
        "/api/v1/auth/login",
        json={"email": "SECURITY-ADMIN@example.com", "password": "SecureAdminPassword123!"},
    )
    duplicate_bootstrap = await client.post(
        "/api/v1/auth/bootstrap-management",
        headers={"X-Bootstrap-Token": "test-management-bootstrap-token"},
        json={**bootstrap_payload(), "email": "second-admin@example.com", "employee_code": "SEC-002"},
    )

    assert me.status_code == 200
    assert logged_in.status_code == 200
    assert duplicate_bootstrap.status_code == 409


@pytest.mark.asyncio
async def test_resident_registration_requires_preprovisioned_profile_and_bearer_wins(client, admin_auth):
    resident = await client.post(
        "/api/v1/residents",
        headers=admin_auth["headers"],
        json={
            "resident_code": "RES-JWT-001",
            "full_name": "Tran Minh Anh",
            "email": "minh.anh@example.com",
            "phone": "0900000099",
        },
    )
    unit = await client.post(
        "/api/v1/units",
        headers=admin_auth["headers"],
        json={"project_code": "ONB", "building": "C", "floor": "3", "unit_number": "C-0301"},
    )
    await client.post(
        f"/api/v1/residents/{resident.json()['id']}/units",
        headers=admin_auth["headers"],
        json={"unit_id": unit.json()["id"], "role": "owner", "is_primary": True},
    )

    registered = await client.post(
        "/api/v1/auth/register/resident",
        json={
            "resident_code": "RES-JWT-001",
            "email": "minh.anh@example.com",
            "password": "ResidentPassword123!",
        },
    )
    invalid_registration = await client.post(
        "/api/v1/auth/register/resident",
        json={
            "resident_code": "UNKNOWN",
            "email": "unknown@example.com",
            "password": "ResidentPassword123!",
        },
    )
    resident_headers = {
        "Authorization": f"Bearer {registered.json()['access_token']}",
        "X-Actor-Role": "management",
        "X-Actor-Id": "spoofed-admin",
    }
    profile = await client.get("/api/v1/residents/me", headers=resident_headers)
    forbidden = await client.get("/api/v1/management/dashboard", headers=resident_headers)

    assert registered.status_code == 201
    assert invalid_registration.status_code == 403
    assert profile.status_code == 200
    assert profile.json()["resident_code"] == "RES-JWT-001"
    assert forbidden.status_code == 403


@pytest.mark.asyncio
async def test_refresh_rotation_detects_reuse_and_revokes_token_family(client, admin_auth):
    rotated = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": admin_auth["refresh_token"]},
    )
    assert rotated.status_code == 200

    reused = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": admin_auth["refresh_token"]},
    )
    current_access = rotated.json()["access_token"]
    me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {current_access}"},
    )

    assert reused.status_code == 401
    assert me.status_code == 401


@pytest.mark.asyncio
async def test_change_password_revokes_existing_tokens(client, admin_auth):
    changed = await client.post(
        "/api/v1/auth/change-password",
        headers=admin_auth["headers"],
        json={
            "current_password": "AdminPassword123!",
            "new_password": "NewAdminPassword456!",
        },
    )
    old_access = await client.get("/api/v1/auth/me", headers=admin_auth["headers"])
    old_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "AdminPassword123!"},
    )
    new_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "NewAdminPassword456!"},
    )

    assert changed.status_code == 204
    assert old_access.status_code == 401
    assert old_login.status_code == 401
    assert new_login.status_code == 200


@pytest.mark.asyncio
async def test_password_reset_sends_non_enumerating_email_and_revokes_tokens(client, admin_auth, monkeypatch):
    sent: dict[str, str] = {}

    def capture_email(_service, recipient: str, raw_token: str) -> None:
        sent["recipient"] = recipient
        sent["token"] = raw_token

    monkeypatch.setattr(EmailService, "send_password_reset_email", capture_email)
    requested = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "ADMIN@example.com"},
    )
    unknown = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "missing@example.com"},
    )

    assert requested.status_code == 202
    assert unknown.status_code == 202
    assert requested.json() == unknown.json()
    assert sent["recipient"] == "admin@example.com"

    reset = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": sent["token"], "new_password": "ResetAdminPassword789!"},
    )
    old_access = await client.get("/api/v1/auth/me", headers=admin_auth["headers"])
    new_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ResetAdminPassword789!"},
    )
    reused = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": sent["token"], "new_password": "AnotherPassword789!"},
    )

    assert reset.status_code == 204
    assert old_access.status_code == 401
    assert new_login.status_code == 200
    assert reused.status_code == 401
