"""Fixtures for PostgreSQL-backed integration tests.

These tests only run when ``TEST_DATABASE_URL`` and
``TEST_MIGRATION_DATABASE_URL`` point at a disposable database. Each test
truncates the tenant tables first, so the suite is repeatable.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.main import create_app
from app.modules.identity.models import College, User
from app.modules.institution.models import Batch, Department, Mentor, Student
from tests.integration.factories import (
    TEST_PASSWORD,
    make_batch,
    make_college,
    make_department,
    make_mentor,
    make_student,
    make_user,
)

BACKEND_ROOT = Path(__file__).resolve().parents[2]
APP_URL = os.environ.get("TEST_DATABASE_URL")
OWNER_URL = os.environ.get("TEST_MIGRATION_DATABASE_URL")

TRUNCATE_TABLES = (
    "audit_logs, mentor_batch_assignments, mentors, students, batches, "
    "departments, user_roles, user_sessions, users, colleges"
)


def require_database() -> None:
    if not APP_URL or not OWNER_URL:
        pytest.skip(
            "TEST_DATABASE_URL and TEST_MIGRATION_DATABASE_URL are required "
            "for integration tests"
        )


@pytest.fixture(scope="session")
def migrated_database() -> Iterator[None]:
    require_database()
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
        env={
            **os.environ,
            "DATABASE_URL": APP_URL,
            "MIGRATION_DATABASE_URL": OWNER_URL,
            "ENVIRONMENT": "test",
            "LOG_JSON": "false",
            "LOG_LEVEL": "WARNING",
        },
    )
    assert result.returncode == 0, result.stdout + result.stderr
    yield None


@pytest.fixture(scope="session")
def owner_engine(migrated_database: None) -> Iterator[Engine]:
    engine = create_engine(OWNER_URL, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def app_engine(migrated_database: None) -> Iterator[Engine]:
    engine = create_engine(APP_URL, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture()
def db(owner_engine: Engine) -> Iterator[Session]:
    with owner_engine.begin() as connection:
        connection.execute(text(f"TRUNCATE {TRUNCATE_TABLES} CASCADE"))
    with Session(owner_engine, expire_on_commit=False) as session:
        yield session


@dataclass(slots=True)
class Tenant:
    college: College
    cse: Department
    ece: Department
    batch_2023: Batch
    batch_2024: Batch
    ece_batch: Batch
    admin: User
    mentor: User
    mentor_row: Mentor
    student_2023: Student
    student_2024: Student
    student_ece: Student
    admin_email: str
    mentor_email: str
    student_2023_email: str
    student_2024_email: str
    student_ece_email: str


@dataclass(slots=True)
class World:
    a: Tenant
    b: Tenant


def _seed_tenant(session: Session, *, short_code: str, name: str) -> Tenant:
    prefix = short_code.lower()
    domain = f"{prefix}.example.edu"
    college = make_college(session, short_code=short_code, name=name, domain=domain)
    cse = make_department(session, college, "CSE")
    ece = make_department(session, college, "ECE")
    batch_2023 = make_batch(
        session, college, cse, name="2023-2027", start_year=2023, end_year=2027
    )
    batch_2024 = make_batch(
        session, college, cse, name="2024-2028", start_year=2024, end_year=2028
    )
    ece_batch = make_batch(
        session, college, ece, name="2023-2027", start_year=2023, end_year=2027
    )

    admin = make_user(
        session,
        college,
        email=f"admin@{domain}",
        roles=("COLLEGE_ADMIN",),
        display_name=f"{short_code} Admin",
    )
    mentor, mentor_row = make_mentor(
        session,
        college,
        cse,
        email=f"mentor@{domain}",
        employee_code=f"{short_code}-M-001",
        batches=(batch_2023,),
    )
    student_2023_user, student_2023 = make_student(
        session,
        college,
        cse,
        batch_2023,
        email=f"student2023@{domain}",
        register_number=f"{short_code}-CSE-001",
    )
    student_2024_user, student_2024 = make_student(
        session,
        college,
        cse,
        batch_2024,
        email=f"student2024@{domain}",
        register_number=f"{short_code}-CSE-002",
    )
    student_ece_user, student_ece = make_student(
        session,
        college,
        ece,
        ece_batch,
        email=f"studentece@{domain}",
        register_number=f"{short_code}-ECE-001",
    )
    return Tenant(
        college=college,
        cse=cse,
        ece=ece,
        batch_2023=batch_2023,
        batch_2024=batch_2024,
        ece_batch=ece_batch,
        admin=admin,
        mentor=mentor,
        mentor_row=mentor_row,
        student_2023=student_2023,
        student_2024=student_2024,
        student_ece=student_ece,
        admin_email=admin.institutional_email,
        mentor_email=mentor.institutional_email,
        student_2023_email=student_2023_user.institutional_email,
        student_2024_email=student_2024_user.institutional_email,
        student_ece_email=student_ece_user.institutional_email,
    )


@pytest.fixture()
def world(db: Session) -> World:
    a = _seed_tenant(db, short_code="TENA", name="Tenant A Institute")
    b = _seed_tenant(db, short_code="TENB", name="Tenant B Institute")
    db.commit()
    return World(a=a, b=b)


@pytest.fixture()
def settings() -> Settings:
    require_database()
    return Settings(
        _env_file=None,
        environment="test",
        database_url=APP_URL,
        migration_database_url=OWNER_URL,
        jwt_secret="integration-test-signing-secret-that-is-long",
        cookie_secure=False,
        log_json=False,
        log_level="WARNING",
        login_max_failures=3,
        login_lockout_minutes=15,
    )


@pytest.fixture()
def app(settings: Settings) -> FastAPI:
    return create_app(settings)


@pytest.fixture()
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def login(app: FastAPI) -> Iterator[Callable[..., TestClient]]:
    clients: list[TestClient] = []

    def _login(
        college_code: str,
        email: str,
        password: str = TEST_PASSWORD,
    ) -> TestClient:
        test_client = TestClient(app)
        test_client.__enter__()
        clients.append(test_client)
        response = test_client.post(
            "/api/v1/auth/login",
            json={
                "college_code": college_code,
                "email": email,
                "password": password,
            },
        )
        assert response.status_code == 200, response.text
        return test_client

    yield _login

    for test_client in clients:
        test_client.__exit__(None, None, None)
