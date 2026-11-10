"""Integration tests for PostgreSQL row-level security (FR-12)."""

from __future__ import annotations

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from app.modules.institution.models import Student
from tests.integration.conftest import World


def set_tenant(connection, college_id) -> None:
    connection.execute(
        text("SELECT set_config('app.current_college_id', :college_id, true)"),
        {"college_id": str(college_id)},
    )


def test_rls_fails_closed_without_a_tenant(app_engine: Engine, world: World) -> None:
    with app_engine.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM users")) == 0
        assert connection.scalar(text("SELECT count(*) FROM departments")) == 0
        assert connection.scalar(text("SELECT count(*) FROM students")) == 0

        set_tenant(connection, world.a.college.id)

        assert connection.scalar(text("SELECT count(*) FROM users")) == 5
        assert connection.scalar(text("SELECT count(*) FROM departments")) == 2
        assert connection.scalar(text("SELECT count(*) FROM students")) == 3


def test_rls_scopes_each_tenant_to_its_own_rows(app_engine: Engine, world: World) -> None:
    with app_engine.connect() as connection:
        set_tenant(connection, world.b.college.id)

        visible_colleges = connection.scalars(text("SELECT short_code FROM colleges")).all()
        assert visible_colleges == ["TENB"]
        assert connection.scalar(text("SELECT count(*) FROM users")) == 5
        assert (
            connection.scalar(
                text("SELECT count(*) FROM users WHERE college_id <> :college_id"),
                {"college_id": str(world.b.college.id)},
            )
            == 0
        )


def test_colleges_require_tenant_or_explicit_system_context(
    app_engine: Engine,
    world: World,
) -> None:
    with app_engine.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM colleges")) == 0

        connection.execute(text("SELECT set_config('app.is_system', 'true', true)"))
        assert connection.scalar(text("SELECT count(*) FROM colleges")) == 2


def test_rls_blocks_cross_tenant_insert(app_engine: Engine, world: World) -> None:
    with app_engine.connect() as connection:
        transaction = connection.begin()
        set_tenant(connection, world.a.college.id)

        with pytest.raises(DBAPIError):
            connection.execute(
                text(
                    "INSERT INTO departments (college_id, code, name) "
                    "VALUES (:college_id, 'XXX', 'Cross tenant')"
                ),
                {"college_id": str(world.b.college.id)},
            )

        transaction.rollback()


def test_composite_foreign_key_blocks_cross_tenant_reference(
    db: Session,
    world: World,
) -> None:
    db.add(
        Student(
            college_id=world.a.college.id,
            user_id=world.a.student_2023.user_id,
            register_number="TENA-XTEN-001",
            department_id=world.a.cse.id,
            batch_id=world.b.batch_2023.id,
            status="ACTIVE",
        )
    )

    with pytest.raises(IntegrityError):
        db.flush()

    db.rollback()


def test_audit_logs_are_append_only_for_the_app_role(
    app_engine: Engine,
    world: World,
) -> None:
    with app_engine.connect() as connection:
        transaction = connection.begin()
        set_tenant(connection, world.a.college.id)
        connection.execute(
            text(
                "INSERT INTO audit_logs (college_id, action, entity_type) "
                "VALUES (:college_id, 'rls.test', 'test')"
            ),
            {"college_id": str(world.a.college.id)},
        )

        with pytest.raises(DBAPIError):
            connection.execute(text("UPDATE audit_logs SET action = 'tampered'"))

        transaction.rollback()


def test_app_role_cannot_delete_audit_logs(app_engine: Engine, world: World) -> None:
    with app_engine.connect() as connection:
        transaction = connection.begin()
        set_tenant(connection, world.a.college.id)

        with pytest.raises(DBAPIError):
            connection.execute(text("DELETE FROM audit_logs"))

        transaction.rollback()


def test_app_role_cannot_modify_the_role_catalogue(
    app_engine: Engine,
    world: World,
) -> None:
    with app_engine.connect() as connection:
        transaction = connection.begin()

        with pytest.raises(DBAPIError):
            connection.execute(text("DELETE FROM roles"))

        transaction.rollback()
