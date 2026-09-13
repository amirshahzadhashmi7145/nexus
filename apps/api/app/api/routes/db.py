from fastapi import APIRouter

from app.db.session import database_status
from app.schemas_db import DbStatusOut

router = APIRouter(prefix="/db", tags=["db"])


@router.get("/status", response_model=DbStatusOut)
def get_db_status() -> DbStatusOut:
    return DbStatusOut(**database_status())
