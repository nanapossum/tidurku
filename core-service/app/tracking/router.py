from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from ..analysis.service import score_sessions
from ..database import get_db
from ..identity.deps import get_current_user
from ..identity.models import User
from ..openapi import ERROR_RESPONSES
from . import service
from .models import SleepSession
from .schemas import SleepSessionIn, SleepSessionListOut, SleepSessionOut


router = APIRouter(
    prefix="/api/sleep-sessions",
    tags=["Tracking"],
    responses=ERROR_RESPONSES,
)


def _with_score(session: SleepSession, score: int | None) -> SleepSessionOut:
    response = SleepSessionOut.model_validate(session)
    return response.model_copy(update={"score": score})


@router.post(
    "",
    response_model=SleepSessionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Catat sesi tidur",
    description="Menyimpan sesi tidur dan mengembalikan skor sesi.",
)
def create_sleep_session(
    data: SleepSessionIn,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> SleepSessionOut:
    session = service.create_session(db, current_user, data)
    score = score_sessions(db, current_user, [session]).get(session.id)
    return _with_score(session, score)


@router.get(
    "",
    response_model=SleepSessionListOut,
    summary="Daftar sesi tidur",
    description="Mengambil sesi milik pengguna, diurutkan dari waktu mulai terbaru.",
)
def list_sleep_sessions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    date_from: Annotated[date | None, Query(alias="from")] = None,
    date_to: Annotated[date | None, Query(alias="to")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> SleepSessionListOut:
    items, total = service.list_sessions(
        db,
        current_user,
        date_from,
        date_to,
        limit,
        offset,
    )
    scores = score_sessions(db, current_user, items)
    return SleepSessionListOut(
        items=[_with_score(item, scores.get(item.id)) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{session_id}",
    response_model=SleepSessionOut,
    summary="Lihat sesi tidur",
    description="Mengambil satu sesi tidur milik pengguna yang sedang terautentikasi.",
)
def get_sleep_session(
    session_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> SleepSessionOut:
    session = service.get_session(db, current_user, session_id)
    score = score_sessions(db, current_user, [session]).get(session.id)
    return _with_score(session, score)


@router.put(
    "/{session_id}",
    response_model=SleepSessionOut,
    summary="Perbarui sesi tidur",
    description="Mengganti data sesi tidur dan menghitung ulang skornya.",
)
def update_sleep_session(
    session_id: str,
    data: SleepSessionIn,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> SleepSessionOut:
    session = service.update_session(db, current_user, session_id, data)
    score = score_sessions(db, current_user, [session]).get(session.id)
    return _with_score(session, score)


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Hapus sesi tidur",
    description="Menghapus sesi tidur milik pengguna.",
)
def delete_sleep_session(
    session_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    service.delete_session(db, current_user, session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
