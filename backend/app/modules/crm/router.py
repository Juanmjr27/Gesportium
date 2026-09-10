import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rate_limit import permitir
from app.modules.crm import service
from app.modules.crm.models import Lead
from app.modules.crm.schemas import (
    InteraccionLeadCreate,
    InteraccionLeadOut,
    LeadConvertir,
    LeadCreate,
    LeadOut,
    LeadUpdate,
)
from app.modules.identidad.dependencies import require_roles, verificar_acceso_por_sede
from app.modules.identidad.models import Usuario
from app.modules.sedes.models import Sede
from app.modules.socios.schemas import SocioDetail

router = APIRouter(prefix="/leads", tags=["crm"])

# POST /leads es anónimo (captura pública de leads): límite básico por IP
# para mitigar spam/abuso, igual de espíritu que el bloqueo de intentos de
# login del módulo 001 pero sin persistir en BD (no hay usuario al que ligar
# la auditoría todavía).
_LEADS_MAX_PETICIONES = 5
_LEADS_VENTANA_MINUTOS = 10


def _obtener_lead_o_404(db: Session, lead_id: uuid.UUID) -> Lead:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead no encontrado")
    return lead


@router.post("", response_model=LeadOut, status_code=status.HTTP_201_CREATED)
def crear_lead(body: LeadCreate, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "desconocida"
    if not permitir(ip, max_peticiones=_LEADS_MAX_PETICIONES, ventana_minutos=_LEADS_VENTANA_MINUTOS):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiadas solicitudes, inténtelo de nuevo más tarde",
        )

    if db.get(Sede, body.sede_interes_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sede no encontrada")

    return service.crear_lead(db, body)


@router.get("", response_model=list[LeadOut])
def listar_leads(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede", "comercial")),
):
    if usuario.rol == "admin":
        return db.query(Lead).all()
    if usuario.rol == "gestor_sede":
        return db.query(Lead).filter(Lead.sede_interes_id == usuario.sede_id).all()
    return db.query(Lead).filter(Lead.comercial_id == usuario.id).all()


@router.put("/{lead_id}", response_model=LeadOut)
def editar_lead(
    lead_id: uuid.UUID,
    body: LeadUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede", "comercial")),
):
    lead = _obtener_lead_o_404(db, lead_id)
    verificar_acceso_por_sede(usuario, lead.sede_interes_id, propietario_id=lead.comercial_id, rol_propietario="comercial")

    cambios = body.model_dump(exclude_unset=True)
    if cambios.get("estado") == "convertido":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El estado 'convertido' solo puede alcanzarse mediante POST /leads/{lead_id}/convertir",
        )
    if usuario.rol == "comercial" and "comercial_id" in cambios:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puede reasignar el lead a otro comercial")

    if "comercial_id" in cambios and cambios["comercial_id"] is not None:
        nuevo_comercial = db.get(Usuario, cambios["comercial_id"])
        if nuevo_comercial is None or nuevo_comercial.rol != "comercial":
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="comercial_id inválido: debe existir y tener rol 'comercial'")

    for campo, valor in cambios.items():
        setattr(lead, campo, valor)
    db.commit()
    db.refresh(lead)
    return lead


@router.post("/{lead_id}/interacciones", response_model=InteraccionLeadOut, status_code=status.HTTP_201_CREATED)
def registrar_interaccion(
    lead_id: uuid.UUID,
    body: InteraccionLeadCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("comercial")),
):
    lead = _obtener_lead_o_404(db, lead_id)
    if lead.comercial_id != usuario.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre este lead")

    return service.registrar_interaccion(db, lead, body, autor_id=usuario.id)


@router.post("/{lead_id}/convertir", response_model=SocioDetail, status_code=status.HTTP_201_CREATED)
def convertir_lead(
    lead_id: uuid.UUID,
    body: LeadConvertir,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede")),
):
    lead = _obtener_lead_o_404(db, lead_id)
    if usuario.rol == "gestor_sede" and usuario.sede_id != lead.sede_interes_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre este lead")
    if lead.estado == "convertido":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El lead ya fue convertido")

    try:
        return service.convertir_a_socio(db, lead, body, autor_id=usuario.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
