"""Integration tests for authentication, sessions and lockout (FR-01/02/08)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.integration.conftest import World
from tests.integration.factories import TEST_PASSWORD


def test_login_sets_httponly_cookie_and_me_returns_roles(
    client: TestClient,
    world: World,
) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "college_code": "TENA",
            "email": world.a.admin_email,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == world.a.admin_email
    assert body["college_code"] == "TENA"
    assert body["roles"] == ["COLLEGE_ADMIN"]

    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "pa_session=" in cookie

    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["user_id"] == body["user_id"]


def test_login_case_insensitive_email_and_college_code(
    client: TestClient,
    world: World,
) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "college_code": " tena ",
            "email": world.a.admin_email.upper(),
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200


def test_login_rejects_wrong_password_without_a_session(
    client: TestClient,
    world: World,
) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "college_code": "TENA",
            "email": world.a.admin_email,
            "password": "WrongPassword1",
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"
    assert "set-cookie" not in response.headers
    assert client.get("/api/v1/auth/me").status_code == 401


def test_login_rejects_unknown_college_and_unknown_user(
    client: TestClient,
    world: World,
) -> None:
    unknown_college = client.post(
        "/api/v1/auth/login",
        json={
            "college_code": "NOPE",
            "email": world.a.admin_email,
            "password": TEST_PASSWORD,
        },
    )
    unknown_user = client.post(
        "/api/v1/auth/login",
        json={
            "college_code": "TENA",
            "email": "missing@tena.example.edu",
            "password": TEST_PASSWORD,
        },
    )

    assert unknown_college.status_code == 401
    assert unknown_user.status_code == 401


def test_invited_user_cannot_use_password_login(
    client: TestClient,
    world: World,
    db: Session,
) -> None:
    world.a.admin.status = "INVITED"
    db.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "college_code": "TENA",
            "email": world.a.admin_email,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 401


def test_repeated_failures_lock_the_account(
    client: TestClient,
    world: World,
) -> None:
    payload = {
        "college_code": "TENA",
        "email": world.a.admin_email,
        "password": "WrongPassword1",
    }

    for _ in range(3):
        assert client.post("/api/v1/auth/login", json=payload).status_code == 401

    locked = client.post(
        "/api/v1/auth/login",
        json={**payload, "password": TEST_PASSWORD},
    )

    assert locked.status_code == 423
    assert locked.json()["error"]["code"] == "account_locked"


def test_logout_revokes_the_server_side_session(
    client: TestClient,
    world: World,
) -> None:
    client.post(
        "/api/v1/auth/login",
        json={
            "college_code": "TENA",
            "email": world.a.admin_email,
            "password": TEST_PASSWORD,
        },
    )
    assert client.get("/api/v1/auth/me").status_code == 200

    assert client.post("/api/v1/auth/logout").status_code == 204

    assert client.get("/api/v1/auth/me").status_code == 401


def test_suspending_a_user_revokes_existing_sessions(
    login,
    world: World,
) -> None:
    admin_client = login("TENA", world.a.admin_email)
    mentor_client = login("TENA", world.a.mentor_email)
    assert mentor_client.get("/api/v1/auth/me").status_code == 200

    response = admin_client.patch(
        f"/api/v1/admin/users/{world.a.mentor.id}/status",
        json={"status": "SUSPENDED"},
    )

    assert response.status_code == 204
    assert mentor_client.get("/api/v1/auth/me").status_code == 401


def test_me_requires_a_session(client: TestClient, world: World) -> None:
    assert client.get("/api/v1/auth/me").status_code == 401


def test_admin_cannot_suspend_own_account(
    login,
    world: World,
) -> None:
    admin_client = login("TENA", world.a.admin_email)

    response = admin_client.patch(
        f"/api/v1/admin/users/{world.a.admin.id}/status",
        json={"status": "SUSPENDED"},
    )

    assert response.status_code == 409


def test_status_update_is_limited_to_the_tenant(
    login,
    world: World,
) -> None:
    admin_client = login("TENA", world.a.admin_email)

    response = admin_client.patch(
        f"/api/v1/admin/users/{world.b.admin.id}/status",
        json={"status": "SUSPENDED"},
    )

    assert response.status_code == 404
