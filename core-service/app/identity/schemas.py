from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)
from pydantic.alias_generators import to_camel


class IdentitySchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        extra="forbid",
    )


class RegisterIn(IdentitySchema):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Nara",
                    "email": "nara@example.com",
                    "password": "contoh-password-aman",
                    "age": 21,
                    "city": "Bandung",
                }
            ]
        }
    )
    name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    password: str
    age: int = Field(ge=10, le=120)
    city: str | None = Field(default=None, max_length=60)

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        try:
            length = len(value.encode("utf-8"))
        except UnicodeEncodeError as error:
            raise ValueError("Password harus berupa teks UTF-8.") from error
        if not 8 <= length <= 72:
            raise ValueError("Password harus berukuran 8–72 byte UTF-8.")
        return value


class LoginIn(IdentitySchema):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "nara@example.com",
                    "password": "contoh-password-aman",
                }
            ]
        }
    )
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        try:
            length = len(value.encode("utf-8"))
        except UnicodeEncodeError as error:
            raise ValueError("Password harus berupa teks UTF-8.") from error
        if length > 72:
            raise ValueError("Password tidak boleh lebih dari 72 byte UTF-8.")
        return value


class UserOut(IdentitySchema):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "c0a80101-0000-4000-8000-000000000001",
                    "name": "Nara",
                    "email": "nara@example.com",
                    "age": 21,
                    "city": "Bandung",
                }
            ]
        }
    )
    id: str
    name: str
    email: EmailStr
    age: int
    city: str | None


class TokenOut(IdentitySchema):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "accessToken": "<token>",
                    "tokenType": "bearer",
                    "expiresIn": 7200,
                    "user": {
                        "id": "c0a80101-0000-4000-8000-000000000001",
                        "name": "Nara",
                        "email": "nara@example.com",
                        "age": 21,
                        "city": "Bandung",
                    },
                }
            ]
        }
    )
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserOut


class UserUpdate(IdentitySchema):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"name": "Nara", "city": None}]}
    )
    name: str | None = Field(default=None, min_length=1, max_length=80)
    age: int | None = Field(default=None, ge=10, le=120)
    city: str | None = Field(default=None, max_length=60)

    @model_validator(mode="after")
    def validate_update(self) -> "UserUpdate":
        supplied = self.model_fields_set
        if not supplied:
            raise ValueError("Setidaknya satu field harus dikirim.")
        if "name" in supplied and self.name is None:
            raise ValueError("Nama tidak boleh null.")
        if "age" in supplied and self.age is None:
            raise ValueError("Usia tidak boleh null.")
        return self
