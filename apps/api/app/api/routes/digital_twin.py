from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas_twin import DigitalTwinOut
from app.services.digital_twin import build_digital_twin

router = APIRouter(tags=["digital-twin"])


@router.get("/digital-twin", response_model=DigitalTwinOut)
def get_digital_twin(db: Session = Depends(get_db)) -> DigitalTwinOut:
    return build_digital_twin(db)
