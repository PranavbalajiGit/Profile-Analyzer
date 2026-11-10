"""Auth request/response schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    college_code: str = Field(min_length=1, max_length=32)
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=256)


class MeResponse(BaseModel):
    user_id: UUID
    college_id: UUID
    college_name: str
    college_code: str
    email: str
    display_name: str
    status: str
    roles: list[str]


class OidcStartResponse(BaseModel):
    authorization_url: str


class AuthConfigResponse(BaseModel):
    oidc_enabled: bool
