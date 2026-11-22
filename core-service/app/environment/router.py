from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..identity.deps import get_current_user
from ..identity.models import User
from ..openapi import ERROR_RESPONSES
from .openmeteo import OpenMeteoAdapter
from .schemas import EnvironmentInsightOut
from .service import get_environment_insights


router = APIRouter(
    prefix="/api/insights/environment",
    tags=["Environment"],
    responses=ERROR_RESPONSES,
)


def get_openmeteo_adapter() -> Iterator[OpenMeteoAdapter]:
    adapter = OpenMeteoAdapter()
    try:
        yield adapter
    finally:
        adapter.close()


@router.get(
    "",
    response_model=EnvironmentInsightOut,
    summary="Lihat insight lingkungan",
    description=(
        "Menghitung korelasi suhu malam, kafein, dan durasi layar dengan skor tidur. "
        "Korelasi tidak menyatakan sebab-akibat."
    ),
)
def read_environment_insights(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    adapter: Annotated[OpenMeteoAdapter, Depends(get_openmeteo_adapter)],
) -> dict[str, object]:
    return get_environment_insights(db, current_user, adapter)
