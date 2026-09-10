import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.identidad.dependencies import require_roles, verificar_acceso_por_sede
from app.modules.identidad.models import Usuario
from app.modules.sedes import service
from app.modules.sedes.models import Sede
from app.modules.sedes.schemas import SedeCreate, SedeDetail, SedePublic, SedeUpdate

router = APIRouter(prefix="/sedes", tags=["sedes"])


def _obtener_sede_o_404(db: Session, sede_id: uuid.UUID) -> Sede:
    sede = db.get(Sede, sede_id)
    if sede is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sede no encontrada")
    return sede


@router.get("", response_model=list[SedePublic])
def listar_sedes_publico(db: Session = Depends(get_db)):
    return db.query(Sede).filter(Sede.activa.is_(True)).all()


@router.get("/{sede_id}", response_model=SedeDetail)
def obtener_sede(
    sede_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede")),
):
    verificar_acceso_por_sede(usuario, sede_id)
    return _obtener_sede_o_404(db, sede_id)


@router.post("", response_model=SedeDetail, status_code=status.HTTP_201_CREATED)
def crear_sede(
    body: SedeCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin")),
):
    sede = Sede(**body.model_dump())
    db.add(sede)
    db.commit()
    db.refresh(sede)
    return sede


@router.put("/{sede_id}", response_model=SedeDetail)
def editar_sede(
    sede_id: uuid.UUID,
    body: SedeUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede")),
):
    verificar_acceso_por_sede(usuario, sede_id)
    sede = _obtener_sede_o_404(db, sede_id)

    for campo, valor in body.model_dump(exclude_unset=True).items():
        setattr(sede, campo, valor)

    db.commit()
    db.refresh(sede)
    return sede


@router.delete("/{sede_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_sede(
    sede_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin")),
):
    sede = _obtener_sede_o_404(db, sede_id)

    if service.tiene_socios_activos(db, sede_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar una sede con socios activos asociados",
        )

    sede.activa = False
    db.commit()
