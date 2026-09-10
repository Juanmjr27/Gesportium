import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.clases import service as clases_service
from app.modules.entrenadores import service
from app.modules.entrenadores.models import Entrenador, SocioAsignado
from app.modules.entrenadores.schemas import (
    BajaEntrenadorBody,
    ClaseFuturaAfectadaOut,
    EntrenadorCreate,
    EntrenadorListItem,
    EntrenadorOut,
    EntrenadorUpdate,
    SocioAsignadoCreate,
    SocioAsignadoOut,
)
from app.modules.identidad import service as identidad_service
from app.modules.identidad.dependencies import require_roles, verificar_acceso_por_sede
from app.modules.identidad.models import Usuario
from app.modules.sedes.models import Sede
from app.modules.socios import service as socios_service

router = APIRouter(prefix="/entrenadores", tags=["entrenadores"])


def _obtener_entrenador_o_404(db: Session, entrenador_id: uuid.UUID) -> Entrenador:
    entrenador = db.get(Entrenador, entrenador_id)
    if entrenador is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrenador no encontrado")
    return entrenador


@router.post("", response_model=EntrenadorOut, status_code=status.HTTP_201_CREATED)
def crear_entrenador(
    body: EntrenadorCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede")),
):
    if usuario.rol == "gestor_sede" and usuario.sede_id != body.sede_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre esta sede")

    if db.get(Sede, body.sede_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sede no encontrada")

    if db.query(Usuario).filter(Usuario.email == body.email).first() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El email ya está registrado")

    usuario_entrenador = identidad_service.crear_usuario(db, body.email, body.password, "entrenador", body.sede_id)

    entrenador = Entrenador(
        usuario_id=usuario_entrenador.id,
        sede_id=body.sede_id,
        especialidades=body.especialidades,
        horario_disponible=body.horario_disponible,
    )
    db.add(entrenador)
    db.commit()
    db.refresh(entrenador)
    return entrenador


@router.get("", response_model=list[EntrenadorListItem])
def listar_entrenadores(
    sede_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede")),
):
    query = db.query(Entrenador)
    if usuario.rol == "gestor_sede":
        query = query.filter(Entrenador.sede_id == usuario.sede_id)
    elif sede_id is not None:
        query = query.filter(Entrenador.sede_id == sede_id)

    filas = query.join(Usuario, Usuario.id == Entrenador.usuario_id).add_columns(Usuario.email).all()
    return [
        EntrenadorListItem(
            id=entrenador.id,
            usuario_id=entrenador.usuario_id,
            email=email,
            sede_id=entrenador.sede_id,
            especialidades=entrenador.especialidades,
            horario_disponible=entrenador.horario_disponible,
            activo=entrenador.activo,
        )
        for entrenador, email in filas
    ]


@router.get("/{entrenador_id}", response_model=EntrenadorOut)
def obtener_entrenador(
    entrenador_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede", "entrenador")),
):
    entrenador = _obtener_entrenador_o_404(db, entrenador_id)

    if usuario.rol == "entrenador":
        if usuario.id != entrenador.usuario_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre este entrenador")
        return entrenador

    verificar_acceso_por_sede(usuario, entrenador.sede_id)
    return entrenador


@router.put("/{entrenador_id}", response_model=EntrenadorOut)
def editar_entrenador(
    entrenador_id: uuid.UUID,
    body: EntrenadorUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede")),
):
    entrenador = _obtener_entrenador_o_404(db, entrenador_id)
    verificar_acceso_por_sede(usuario, entrenador.sede_id)

    for campo, valor in body.model_dump(exclude_unset=True).items():
        setattr(entrenador, campo, valor)
    db.commit()
    db.refresh(entrenador)
    return entrenador


@router.delete("/{entrenador_id}")
def eliminar_entrenador(
    entrenador_id: uuid.UUID,
    body: BajaEntrenadorBody,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede")),
):
    entrenador = _obtener_entrenador_o_404(db, entrenador_id)
    verificar_acceso_por_sede(usuario, entrenador.sede_id)

    if not entrenador.activo:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El entrenador ya está dado de baja")

    clases_futuras = clases_service.listar_clases_futuras_activas(db, entrenador.id)

    if clases_futuras and not body.confirmar:
        return {
            "requiere_confirmacion": True,
            "clases_futuras": [ClaseFuturaAfectadaOut.model_validate(c) for c in clases_futuras],
            "detail": (
                "El entrenador tiene clases futuras asignadas. Reenvíe la petición con "
                "confirmar=true y decision='reasignar' (con nuevo_entrenador_id) o "
                "decision='cancelar' para completar la baja."
            ),
        }

    if clases_futuras and body.decision is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="decision es obligatorio ('reasignar' o 'cancelar') cuando hay clases futuras asignadas",
        )

    if body.decision == "reasignar":
        nuevo_entrenador = db.get(Entrenador, body.nuevo_entrenador_id)
        if nuevo_entrenador is None or not nuevo_entrenador.activo:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="nuevo_entrenador_id inválido: debe existir y estar activo",
            )

    entrenador = service.dar_baja_entrenador(db, entrenador, body.decision, body.nuevo_entrenador_id)
    return EntrenadorOut.model_validate(entrenador)


@router.post("/{entrenador_id}/socios", response_model=SocioAsignadoOut, status_code=status.HTTP_201_CREATED)
def asignar_socio(
    entrenador_id: uuid.UUID,
    body: SocioAsignadoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede")),
):
    entrenador = _obtener_entrenador_o_404(db, entrenador_id)
    verificar_acceso_por_sede(usuario, entrenador.sede_id)

    if not entrenador.activo:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No se puede asignar socios a un entrenador dado de baja")

    socio = socios_service.obtener_socio(db, body.socio_id)
    if socio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Socio no encontrado")
    if socio.sede_id != entrenador.sede_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El socio no pertenece a la sede del entrenador")

    ya_asignado = (
        db.query(SocioAsignado)
        .filter(
            SocioAsignado.entrenador_id == entrenador_id,
            SocioAsignado.socio_id == body.socio_id,
            SocioAsignado.fecha_fin.is_(None),
        )
        .first()
    )
    if ya_asignado is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El socio ya está asignado a este entrenador")

    return service.asignar_socio(db, entrenador_id, body.socio_id)


@router.delete("/{entrenador_id}/socios/{socio_id}", status_code=status.HTTP_204_NO_CONTENT)
def desasignar_socio(
    entrenador_id: uuid.UUID,
    socio_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede")),
):
    entrenador = _obtener_entrenador_o_404(db, entrenador_id)
    verificar_acceso_por_sede(usuario, entrenador.sede_id)

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignación no encontrada")

    service.desasignar_socio(db, asignacion)


@router.get("/{entrenador_id}/socios", response_model=list[SocioAsignadoOut])
def listar_socios_asignados(
    entrenador_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede", "entrenador")),
):
    entrenador = _obtener_entrenador_o_404(db, entrenador_id)

    if usuario.rol == "entrenador":
        if usuario.id != entrenador.usuario_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre este entrenador")
    elif usuario.rol == "gestor_sede":
        if usuario.sede_id != entrenador.sede_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre este entrenador")

    return (
        db.query(SocioAsignado)
        .filter(SocioAsignado.entrenador_id == entrenador_id, SocioAsignado.fecha_fin.is_(None))
        .all()
    )
