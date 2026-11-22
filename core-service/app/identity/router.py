"""Logout dilakukan klien dengan membuang token; server tidak menyimpan sesi."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..openapi import ERROR_RESPONSES
from ..security import create_access_token
from .deps import get_current_user
from .models import User
from .schemas import LoginIn, RegisterIn, TokenOut, UserOut, UserUpdate
from .service import authenticate_user, register_user, update_user


router = APIRouter(tags=["Identity"], responses=ERROR_RESPONSES)


def _token_response(user: User) -> TokenOut:
    token, expires_in = create_access_token(user.id)
    return TokenOut(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserOut.model_validate(user),
    )


@router.post(
    "/api/auth/register",
    response_model=TokenOut,
    status_code=status.HTTP_201_CREATED,
    summary="Daftarkan akun",
    description="Membuat akun pengguna baru dan mengembalikan token akses.",
)
def register(
    data: RegisterIn,
    db: Annotated[Session, Depends(get_db)],
) -> TokenOut:
    return _token_response(register_user(db, data))


@router.post(
    "/api/auth/login",
    response_model=TokenOut,
    summary="Masuk",
    description="Memvalidasi kredensial dan mengembalikan token akses.",
)
def login(
    data: LoginIn,
    db: Annotated[Session, Depends(get_db)],
) -> TokenOut:
    return _token_response(authenticate_user(db, data))


@router.get(
    "/api/me",
    response_model=UserOut,
    summary="Lihat profil",
    description="Mengembalikan profil pengguna yang sedang terautentikasi.",
)
def read_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserOut:
    return UserOut.model_validate(current_user)


@router.patch(
    "/api/me",
    response_model=UserOut,
    summary="Perbarui profil",
    description="Memperbarui nama, usia, atau kota pengguna; email tidak dapat diubah.",
)
def patch_me(
    data: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UserOut:
    return UserOut.model_validate(update_user(db, current_user, data))
