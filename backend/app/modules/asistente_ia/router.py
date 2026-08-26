import uuid
from datetime import datetime
 
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
 
from app.core.database import get_db
from app.modules.asistente_ia import service
from app.modules.asistente_ia.models import BorradorIA, ConversacionIA, MensajeIA
from app.modules.asistente_ia.schemas import (
    BorradorEditar,
    BorradorOut,
    BorradorRechazar,
    MensajeCreate,
    MensajeOut,
    WizardBorradorRequest,
)
from app.modules.asistente_ia.service import generar_contenido_borrador, generar_respuesta_chat
from app.modules.entrenadores.models import Entrenador, SocioAsignado
from app.modules.entrenamiento import service as entrenamiento_service
from app.modules.identidad.dependencies import require_roles
from app.modules.identidad.models import Usuario
from app.modules.membresias.models import Membresia, PlanMembresia
from app.modules.socios.models import Socio
 
router = APIRouter(prefix="/asistente", tags=["asistente_ia"])
 
 
def _obtener_socio_propio(db: Session, usuario: Usuario) -> Socio:
    socio = db.query(Socio).filter(Socio.usuario_id == usuario.id).first()
    if socio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Socio no encontrado")
    return socio
 
 
def _obtener_entrenador_propio(db: Session, usuario: Usuario) -> Entrenador:
    entrenador = db.query(Entrenador).filter(Entrenador.usuario_id == usuario.id).first()
    if entrenador is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrenador no encontrado")
    return entrenador
 
 
def _validar_asignacion(db: Session, entrenador_id: uuid.UUID, socio_id: uuid.UUID) -> None:
    asignacion = (
        db.query(SocioAsignado)
        .filter(
            SocioAsignado.entrenador_id == entrenador_id,
            SocioAsignado.socio_id == socio_id,
            SocioAsignado.fecha_fin.is_(None),
        )
        .first()
    )
    if asignacion is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="El socio no está asignado a este entrenador")
 
 
@router.post("/mensaje", response_model=MensajeOut, status_code=status.HTTP_201_CREATED)
def enviar_mensaje(
    body: MensajeCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("socio")),
):
    socio = _obtener_socio_propio(db, usuario)
    conversacion = service.obtener_o_crear_conversacion(db, socio.id)
    service.registrar_mensaje(db, conversacion.id, "socio", body.contenido)
 
    mensajes_previos = (
        db.query(MensajeIA)
        .filter(MensajeIA.conversacion_id == conversacion.id)
        .order_by(MensajeIA.fecha)
        .all()
    )
    historial = [f"{'Socio' if m.rol == 'socio' else 'Asistente'}: {m.contenido}" for m in mensajes_previos[:-1]]
 
    respuesta = generar_respuesta_chat(historial, body.contenido)
    if respuesta is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="El asistente no está disponible en este momento"
        )
 
    return service.registrar_mensaje(db, conversacion.id, "asistente", respuesta)
 
 
@router.get("/historial", response_model=list[MensajeOut])
def ver_historial(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("socio")),
):
    socio = _obtener_socio_propio(db, usuario)
    conversacion = db.query(ConversacionIA).filter(ConversacionIA.socio_id == socio.id).first()
    if conversacion is None:
        return []
    return db.query(MensajeIA).filter(MensajeIA.conversacion_id == conversacion.id).order_by(MensajeIA.fecha).all()
 
 
@router.post("/borrador", response_model=BorradorOut, status_code=status.HTTP_201_CREATED)
def solicitar_borrador(
    body: WizardBorradorRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("socio")),
):
    socio = _obtener_socio_propio(db, usuario)
    edad = service.calcular_edad(socio.fecha_nacimiento)
 
    membresia = db.query(Membresia).filter(Membresia.socio_id == socio.id, Membresia.estado == "activa").first()
    plan_nombre = None
    if membresia is not None:
        plan = db.get(PlanMembresia, membresia.plan_id)
        plan_nombre = plan.nombre if plan is not None else None
 
    datos_cuestionario = body.model_dump(exclude_none=True)
 
    contenido = generar_contenido_borrador(body.tipo_borrador, edad, datos_cuestionario, plan_nombre)
    if contenido is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El asistente no pudo generar el borrador, inténtelo de nuevo",
        )
 
    borrador = BorradorIA(
        socio_id=socio.id,
        tipo=body.tipo_borrador,
        datos_cuestionario=datos_cuestionario,
        contenido=contenido,
        estado="pendiente",
    )
    db.add(borrador)
    db.commit()
    db.refresh(borrador)
    return borrador
 
 
@router.get("/borradores-pendientes", response_model=list[BorradorOut])
def listar_borradores_pendientes(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("entrenador")),
):
    # BorradorOut ya incluye datos_cuestionario y motivo_rechazo (T3):
    # el entrenador ve datos del cuestionario + contenido en la misma
    # respuesta, sin tocar esta consulta.
    entrenador = _obtener_entrenador_propio(db, usuario)
    socio_ids = [
        row[0]
        for row in db.query(SocioAsignado.socio_id)
        .filter(SocioAsignado.entrenador_id == entrenador.id, SocioAsignado.fecha_fin.is_(None))
        .all()
    ]
    return (
        db.query(BorradorIA)
        .filter(BorradorIA.estado == "pendiente", BorradorIA.socio_id.in_(socio_ids))
        .all()
    )
 
 
def _obtener_borrador_pendiente_de_socio_asignado(
    db: Session, entrenador: Entrenador, borrador_id: uuid.UUID
) -> BorradorIA:
    borrador = db.get(BorradorIA, borrador_id)
    if borrador is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Borrador no encontrado")
    if borrador.estado != "pendiente":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El borrador ya ha sido revisado")
 
    _validar_asignacion(db, entrenador.id, borrador.socio_id)
    return borrador
 
 
@router.patch("/borradores/{borrador_id}", response_model=BorradorOut)
def editar_borrador(
    borrador_id: uuid.UUID,
    body: BorradorEditar,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("entrenador")),
):
    """Flujo "editar y aprobar" de la spec: el entrenador ajusta el
    contenido del borrador antes de aprobarlo. No cambia `estado` — el
    entrenador llama después a /aprobar."""
    entrenador = _obtener_entrenador_propio(db, usuario)
    borrador = _obtener_borrador_pendiente_de_socio_asignado(db, entrenador, borrador_id)
 
    borrador.contenido = body.contenido
    db.commit()
    db.refresh(borrador)
    return borrador
 
 
@router.post("/borradores/{borrador_id}/aprobar", response_model=BorradorOut)
def aprobar_borrador(
    borrador_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("entrenador")),
):
    entrenador = _obtener_entrenador_propio(db, usuario)
    borrador = _obtener_borrador_pendiente_de_socio_asignado(db, entrenador, borrador_id)
 
    try:
        if borrador.tipo == "rutina":
            entrenamiento_service.crear_rutina_desde_borrador(
                db, entrenador.id, borrador.socio_id, borrador.id, borrador.contenido
            )
        else:
            entrenamiento_service.crear_plan_nutricional_desde_borrador(
                db, entrenador.id, borrador.socio_id, borrador.id, borrador.contenido
            )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
 
    borrador.estado = "aprobado"
    borrador.entrenador_revisor_id = entrenador.id
    borrador.fecha_revision = datetime.utcnow()
    db.commit()
    db.refresh(borrador)
    return borrador
 
 
@router.post("/borradores/{borrador_id}/rechazar", response_model=BorradorOut)
def rechazar_borrador(
    borrador_id: uuid.UUID,
    body: BorradorRechazar,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("entrenador")),
):
    entrenador = _obtener_entrenador_propio(db, usuario)
    borrador = _obtener_borrador_pendiente_de_socio_asignado(db, entrenador, borrador_id)
 
    borrador.estado = "rechazado"
    borrador.motivo_rechazo = body.motivo
    borrador.entrenador_revisor_id = entrenador.id
    borrador.fecha_revision = datetime.utcnow()
    db.commit()
    db.refresh(borrador)
    return borrador