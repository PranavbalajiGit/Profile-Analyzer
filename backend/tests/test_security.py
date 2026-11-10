"""Unit tests for password, token and OIDC-state helpers."""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.core.security import (
    OIDC_STATE_AUDIENCE,
    SESSION_AUDIENCE,
    InvalidTokenError,
    create_oidc_state,
    decode_token,
    encode_token,
    hash_password,
    hash_token,
    password_needs_rehash,
    read_oidc_state,
    validate_password_strength,
    verify_password,
)
from app.modules.auth.oidc import OidcError, read_state


@pytest.fixture()
def settings() -> Settings:
    return Settings(
        _env_file=None,
        environment="test",
        jwt_secret="unit-test-secret-that-is-long-enough",
        log_json=False,
    )


def test_password_hash_round_trip() -> None:
    hashed = hash_password("CorrectHorse1Battery")

    assert hashed != "CorrectHorse1Battery"
    assert verify_password(hashed, "CorrectHorse1Battery") is True
    assert verify_password(hashed, "wrong-password") is False
    assert password_needs_rehash(hashed) is False


def test_verify_password_tolerates_missing_or_broken_hashes() -> None:
    assert verify_password(None, "anything") is False
    assert verify_password("not-an-argon2-hash", "anything") is False


def test_password_policy_reports_each_violation() -> None:
    problems = validate_password_strength("short")

    assert any("12 characters" in problem for problem in problems)
    assert any("uppercase" in problem for problem in problems)
    assert any("digit" in problem for problem in problems)
    assert validate_password_strength("CorrectHorse1Battery") == []


def test_token_hash_is_stable_and_one_way() -> None:
    token = "opaque-session-value"

    assert hash_token(token) == hash_token(token)
    assert hash_token(token) != hash_token("other-value")
    assert len(hash_token(token)) == 32


def test_session_token_round_trip(settings: Settings) -> None:
    user_id = uuid4()
    college_id = uuid4()
    session_id = uuid4()
    token = encode_token(
        {"sub": str(user_id), "col": str(college_id), "sid": str(session_id)},
        settings,
        audience=SESSION_AUDIENCE,
        ttl=timedelta(minutes=5),
    )

    claims = decode_token(token, settings, audience=SESSION_AUDIENCE)

    assert claims["sub"] == str(user_id)
    assert claims["col"] == str(college_id)
    assert claims["sid"] == str(session_id)
    assert claims["iss"] == settings.jwt_issuer


def test_token_audience_is_enforced(settings: Settings) -> None:
    token = encode_token(
        {"col": str(uuid4())},
        settings,
        audience=OIDC_STATE_AUDIENCE,
        ttl=timedelta(minutes=5),
    )

    with pytest.raises(InvalidTokenError):
        decode_token(token, settings, audience=SESSION_AUDIENCE)


def test_tampered_and_expired_tokens_are_rejected(settings: Settings) -> None:
    token = encode_token({}, settings, audience=SESSION_AUDIENCE, ttl=timedelta(minutes=5))
    tampered = token[:-1] + ("a" if token[-1] != "a" else "b")

    with pytest.raises(InvalidTokenError):
        decode_token(tampered, settings, audience=SESSION_AUDIENCE)

    expired = encode_token({}, settings, audience=SESSION_AUDIENCE, ttl=timedelta(seconds=-1))
    with pytest.raises(InvalidTokenError):
        decode_token(expired, settings, audience=SESSION_AUDIENCE)


def test_oidc_state_round_trip_binds_the_college(settings: Settings) -> None:
    college_id = uuid4()
    state = create_oidc_state(college_id=college_id, nonce="nonce-value", settings=settings)

    claims = read_oidc_state(state, settings)
    assert claims["col"] == str(college_id)
    assert claims["nonce"] == "nonce-value"
    assert read_state(settings, state) == college_id


def test_oidc_state_tampering_is_rejected(settings: Settings) -> None:
    state = create_oidc_state(college_id=uuid4(), nonce="nonce-value", settings=settings)

    with pytest.raises(OidcError):
        read_state(settings, state + "x")
