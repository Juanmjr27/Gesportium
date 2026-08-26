import uuid

from sqlalchemy.orm import Session

from app.modules.socios import service as socios_service


def tiene_socios_activos(db: Session, sede_id: uuid.UUID) -> bool:
    return socios_service.tiene_socios_activos(db, sede_id)
