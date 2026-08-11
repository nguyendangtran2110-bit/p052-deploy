from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, StringConstraints

Password = Annotated[str, StringConstraints(min_length=12, max_length=128)]
VerificationCode = Annotated[str, StringConstraints(pattern=r"^\d{6}$")]


class ResidentRegistrationRequest(BaseModel):
    resident_code: str = Field(min_length=2, max_length=50)
    email: EmailStr
    password: Password


class ResidentEmailRequest(BaseModel):
    email: EmailStr


class ResidentEmailVerificationRequest(BaseModel):
    email: EmailStr
    code: VerificationCode


class ManagementBootstrapRequest(BaseModel):
    email: EmailStr
    password: Password
    employee_code: str = Field(min_length=2, max_length=50)
    full_name: str = Field(min_length=2, max_length=255)
    phone: str | None = Field(default=None, max_length=30)
    department: str | None = Field(default=None, max_length=100)
    job_title: str | None = Field(default=None, max_length=100)
    project_code: str | None = Field(default=None, max_length=50)
    building: str | None = Field(default=None, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=4096)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: Password


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20, max_length=4096)
    new_password: Password
