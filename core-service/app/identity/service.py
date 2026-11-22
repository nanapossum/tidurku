from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..errors import AppError
from ..security import DUMMY_HASH, hash_password, verify_password
from .models import User
from .schemas import LoginIn, RegisterIn, UserUpdate


INVALID_CREDENTIALS = "Email atau kata sandi tidak valid."


def register_user(db: Session, data: RegisterIn) -> User:
    email = str(data.email).strip().lower()
    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise AppError(409, "EMAIL_TAKEN", "Email sudah terdaftar.")

    user = User(
        name=data.name,
        email=email,
        password_hash=hash_password(data.password),
        age=data.age,
        city=data.city,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        if db.scalar(select(User.id).where(User.email == email)) is not None:
            raise AppError(409, "EMAIL_TAKEN", "Email sudah terdaftar.") from error
        raise
    db.refresh(user)
    return user


def authenticate_user(db: Session, data: LoginIn) -> User:
    email = str(data.email).strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    password_hash = user.password_hash if user is not None else DUMMY_HASH
    password_matches = verify_password(data.password, password_hash)
    if user is None or not password_matches:
        raise AppError(401, "INVALID_CREDENTIALS", INVALID_CREDENTIALS)
    return user


def update_user(db: Session, user: User, data: UserUpdate) -> User:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user
