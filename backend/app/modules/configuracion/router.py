from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.configuracion import service
from app.modules.configuracion.models import ConfiguracionGlobal
from app.modules.configuracion.schemas import ConfiguracionOut, ConfiguracionUpdate
from app.modules.identidad.dependencies import require_roles
from app.modules.identidad.models import Usuario

router = APIRouter(prefix="/configuracion", tags=["configuracion"])


@router.get("", response_model=list[ConfiguracionOut])
def listar_configuracion(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin")),
):
    return db.query(ConfiguracionGlobal).order_by(ConfiguracionGlobal.clave).all()


@router.put("/{clave}", response_model=ConfiguracionOut)
def editar_configuracion(
    clave: str,
    body: ConfiguracionUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin")),
):
    config = db.get(ConfiguracionGlobal, clave)
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parámetro de configuración no encontrado")

    try:
        return service.editar_configuracion(db, config, body.valor, usuario.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
