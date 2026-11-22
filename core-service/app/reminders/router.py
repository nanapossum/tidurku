from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..identity.deps import get_current_user
from ..identity.models import User
from ..openapi import ERROR_RESPONSES
from .schemas import ReminderOut, ReminderUpdateIn
from .service import get_reminder, update_reminder


router = APIRouter(
    prefix="/api/reminders",
    tags=["Reminders"],
    responses=ERROR_RESPONSES,
)


@router.get(
    "",
    response_model=ReminderOut,
    summary="Lihat pengingat",
    description="Mengembalikan pengaturan pengingat dan waktu yang digunakan.",
)
def read_reminder(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ReminderOut:
    return get_reminder(db, current_user)


@router.put(
    "",
    response_model=ReminderOut,
    summary="Perbarui pengingat",
    description="Menyimpan pengaturan; penjadwalan notifikasi dilakukan aplikasi mobile.",
)
def put_reminder(
    data: ReminderUpdateIn,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ReminderOut:
    """Persist settings only; the mobile app schedules local notifications."""
    return update_reminder(db, current_user, data)
