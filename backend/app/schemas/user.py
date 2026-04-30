import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr

from app.core.password import validate_password_strength
from app.enums.enums import UserRole
from app.schemas.acl import AclBase
from app.schemas.general import BaseFilter

PasswordStr = Annotated[str, AfterValidator(validate_password_strength)]


class UserBase(BaseModel):
    """
    Shared properties for multiple user schemas
    """

    email: EmailStr
    role: UserRole
    disabled: bool

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@raptr.app",
                "role": UserRole.USER,
                "disabled": False,
            }
        },
    )


class UserRead(UserBase):
    """
    Properties to return via API for general user requests
    """

    id: uuid.UUID
    mfa_verified: bool
    last_login_at: datetime | None
    last_logout_at: datetime | None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                **UserBase.model_config.get("json_schema_extra", {}).get("example", {}),
                "id": "00000000-0000-0000-0000-000000000000",
                "mfa_verified": False,
                "last_login_at": "2026-01-25T16:14:55.000Z",
                "last_logout_at": "2026-01-25T16:14:55.000Z",
            }
        },
    )


class UserReadAcl(UserRead):
    """
    Properties to return via API for general user requests, including ACLs
    """

    acl: list[AclBase] | None = []


class UserFilter(BaseFilter):
    """
    Filter schema for user queries. All fields optional.
    """

    email: str | None = None
    role: list[UserRole] | None = None
    disabled: list[bool] | None = None
    mfa_verified: list[bool] | None = None
    sort_by: Literal["email", "role", "disabled", "mfa_verified"] | None = None


class UserCreate(UserBase):
    """
    Properties to receive via API on user creation. Password is required
    """

    password: PasswordStr

    model_config = ConfigDict(
        hide_input_in_errors=True,
        json_schema_extra={
            "example": {
                **UserBase.model_config.get("json_schema_extra", {}).get("example", {}),
                "password": "Password.123",
            }
        },
    )


class UserPasswordUpdate(BaseModel):
    """
    Properties to receive via API on user password update
    """

    new_password: PasswordStr
    old_password: PasswordStr

    model_config = ConfigDict(
        hide_input_in_errors=True,
        json_schema_extra={
            "example": {"new_password": "Password.123", "old_password": "Password.123"}
        },
    )


class UserPasswordReset(BaseModel):
    """
    Properties to receive via API on user password reset
    """

    new_password: PasswordStr

    model_config = ConfigDict(
        hide_input_in_errors=True,
        json_schema_extra={"example": {"new_password": "Password.123"}},
    )


class UserPasswordMfaReset(BaseModel):
    """
    Properties to receive via API on user password MFA reset
    """

    password: PasswordStr

    model_config = ConfigDict(
        hide_input_in_errors=True,
        json_schema_extra={"example": {"password": "Password.123"}},
    )
