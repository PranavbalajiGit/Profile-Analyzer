"""Integration tests for RBAC and tenant scoping (FR-04/09/11/12)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from tests.integration.conftest import World
from tests.integration.factories import TEST_PASSWORD, make_user


def test_mentor_sees_only_students_in_assigned_batches(login, world: World) -> None:
    mentor_client = login("TENA", world.a.mentor_email)

    response = mentor_client.get("/api/v1/students")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert [item["register_number"] for item in body["items"]] == ["TENA-CSE-001"]


def test_college_admin_sees_every_student_in_own_tenant(login, world: World) -> None:
    admin_client = login("TENA", world.a.admin_email)

    response = admin_client.get("/api/v1/students")

    assert response.status_code == 200
    numbers = {item["register_number"] for item in response.json()["items"]}
    assert numbers == {"TENA-CSE-001", "TENA-CSE-002", "TENA-ECE-001"}


def test_student_cannot_list_students(login, world: World) -> None:
    student_client = login("TENA", world.a.student_2023_email)

    response = student_client.get("/api/v1/students")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"


def test_student_can_read_and_update_own_profile(login, world: World) -> None:
    student_client = login("TENA", world.a.student_2023_email)

    me = student_client.get("/api/v1/students/me")
    assert me.status_code == 200
    assert me.json()["register_number"] == "TENA-CSE-001"

    updated = student_client.patch(
        "/api/v1/students/me",
        json={"display_name": "Renamed Synthetic", "current_year": 4},
    )
    assert updated.status_code == 200
    assert updated.json()["display_name"] == "Renamed Synthetic"
    assert updated.json()["current_year"] == 4
    # The re-read after commit proves the RLS setting survives the response path.
    assert student_client.get("/api/v1/students/me").json()["current_year"] == 4


def test_mentor_cannot_use_admin_endpoints(login, world: World) -> None:
    mentor_client = login("TENA", world.a.mentor_email)

    assert mentor_client.get("/api/v1/admin/departments").status_code == 403
    assert mentor_client.get("/api/v1/admin/audit-logs").status_code == 403


def test_tenant_isolation_hides_other_college(login, world: World) -> None:
    admin_a = login("TENA", world.a.admin_email)
    admin_b = login("TENB", world.b.admin_email)

    departments_a = admin_a.get("/api/v1/admin/departments").json()
    departments_b = admin_b.get("/api/v1/admin/departments").json()

    assert {row["id"] for row in departments_a}.isdisjoint({row["id"] for row in departments_b})
    assert all(row["code"] in {"CSE", "ECE"} for row in departments_a)

    students_b = admin_b.get("/api/v1/students").json()["items"]
    assert {item["register_number"] for item in students_b} == {
        "TENB-CSE-001",
        "TENB-CSE-002",
        "TENB-ECE-001",
    }


def test_admin_cannot_update_department_from_another_tenant(login, world: World) -> None:
    admin_a = login("TENA", world.a.admin_email)

    response = admin_a.patch(
        f"/api/v1/admin/departments/{world.b.cse.id}",
        json={"name": "Hijacked"},
    )

    assert response.status_code == 404


def test_department_creation_is_audited(login, world: World) -> None:
    admin_client = login("TENA", world.a.admin_email)

    created = admin_client.post(
        "/api/v1/admin/departments",
        json={"code": "ME", "name": "Mechanical Engineering"},
    )
    assert created.status_code == 201

    audit = admin_client.get("/api/v1/admin/audit-logs")
    assert audit.status_code == 200
    actions = [entry["action"] for entry in audit.json()["items"]]
    assert "department.created" in actions


def test_duplicate_department_code_conflicts(login, world: World) -> None:
    admin_client = login("TENA", world.a.admin_email)

    response = admin_client.post(
        "/api/v1/admin/departments",
        json={"code": "CSE", "name": "Duplicate"},
    )

    assert response.status_code == 409


def test_mentor_provisioning_and_batch_assignment(login, world: World) -> None:
    admin_client = login("TENA", world.a.admin_email)

    created = admin_client.post(
        "/api/v1/admin/mentors",
        json={
            "email": "newmentor@tena.example.edu",
            "display_name": "New Mentor",
            "employee_code": "TENA-M-002",
            "department_id": str(world.a.cse.id),
            "temporary_password": TEST_PASSWORD,
        },
    )
    assert created.status_code == 201, created.text
    mentor = created.json()

    assigned = admin_client.post(
        "/api/v1/admin/mentors/assign",
        json={"mentor_id": mentor["id"], "batch_id": str(world.a.batch_2024.id)},
    )
    assert assigned.status_code == 201, assigned.text

    mentor_client = login("TENA", "newmentor@tena.example.edu")
    response = mentor_client.get("/api/v1/students")
    assert response.status_code == 200
    assert [item["register_number"] for item in response.json()["items"]] == [
        "TENA-CSE-002"
    ]


def test_super_admin_lists_and_creates_colleges(login, world: World, db: Session) -> None:
    super_admin = make_user(
        db,
        world.a.college,
        email="super@platform.example.edu",
        roles=("SUPER_ADMIN",),
        display_name="Platform Super Admin",
    )
    db.commit()

    client = login("TENA", super_admin.institutional_email)

    listed = client.get("/api/v1/admin/colleges")
    assert listed.status_code == 200
    assert {row["short_code"] for row in listed.json()} == {"TENA", "TENB"}

    created = client.post(
        "/api/v1/admin/colleges",
        json={"name": "Tenant C Institute", "short_code": "TENC"},
    )
    assert created.status_code == 201, created.text

    listed_again = client.get("/api/v1/admin/colleges")
    assert {row["short_code"] for row in listed_again.json()} == {
        "TENA",
        "TENB",
        "TENC",
    }


def test_college_admin_cannot_list_colleges(login, world: World) -> None:
    admin_client = login("TENA", world.a.admin_email)

    assert admin_client.get("/api/v1/admin/colleges").status_code == 403
