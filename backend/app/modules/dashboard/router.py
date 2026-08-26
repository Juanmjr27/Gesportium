import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.dashboard import service
from app.modules.dashboard.schemas import DashboardKPIsOut
from app.modules.identidad.dependencies import require_roles
from app.modules.identidad.models import Usuario
from app.modules.sedes.models import Sede

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/kpis", response_model=DashboardKPIsOut)
def obtener_kpis(
    sede_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede")),
):
    if usuario.rol == "gestor_sede":
        if sede_id is not None and sede_id != usuario.sede_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre esta sede")
        sede_id = usuario.sede_id
    elif sede_id is not None and db.get(Sede, sede_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sede no encontrada")

    return service.calcular_kpis(db, sede_id)
