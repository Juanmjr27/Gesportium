import secrets
import uuid

from sqlalchemy.orm import Session

from app.modules.crm.models import InteraccionLead, Lead
from app.modules.crm.schemas import InteraccionLeadCreate, LeadConvertir, LeadCreate
from app.modules.identidad import service as identidad_service
from app.modules.identidad.models import Usuario
from app.modules.socios import service as socios_service
from app.modules.socios.models import Socio
from app.modules.socios.schemas import SocioCreate


def crear_lead(db: Session, body: LeadCreate) -> Lead:
    lead = Lead(**body.model_dump(), estado="nuevo")
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


def registrar_interaccion(db: Session, lead: Lead, body: InteraccionLeadCreate, autor_id: uuid.UUID) -> InteraccionLead:
    interaccion = InteraccionLead(lead_id=lead.id, autor_id=autor_id, **body.model_dump())
    db.add(interaccion)
    db.commit()
    db.refresh(interaccion)
    return interaccion


def convertir_a_socio(db: Session, lead: Lead, body: LeadConvertir, autor_id: uuid.UUID) -> Socio:
    usuario = db.query(Usuario).filter(Usuario.email == lead.email).first()
    if usuario is None:
        # El lead no trae password: se genera una temporal aleatoria: el
        # nuevo socio la restablece vía /auth/forgot-password (001), igual
        # que cualquier alta de cuenta sin invitación por email explícita.
        password_temporal = secrets.token_urlsafe(16)
        usuario = identidad_service.crear_usuario(
            db, lead.email, password_temporal, "socio", lead.sede_interes_id
        )

    if db.query(Socio).filter(Socio.usuario_id == usuario.id).first() is not None:
        raise ValueError("Este email ya está asociado a un socio existente")

    socio_data = SocioCreate(
        usuario_id=usuario.id,
        sede_id=lead.sede_interes_id,
        fecha_nacimiento=body.fecha_nacimiento,
        telefono=lead.telefono,
        direccion=body.direccion,
        contacto_emergencia_nombre=body.contacto_emergencia_nombre,
        contacto_emergencia_telefono=body.contacto_emergencia_telefono,
    )
    socio = socios_service.crear_socio(db, socio_data, autor_id=autor_id)

    lead.estado = "convertido"
    db.commit()
    db.refresh(socio)
    return socio
