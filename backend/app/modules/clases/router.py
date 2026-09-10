import uuid
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.clases import service
from app.modules.clases.models import Clase, Reserva
from app.modules.clases.schemas import (
    ClaseCreate,
    ClaseDetail,
    ClaseListItem,
    ClaseUpdate,
    OcupacionOut,
    ReasignarPorBajaEntrenadorBody,
    ReservaOut,
)
from app.modules.entrenadores.models import Entrenador
from app.modules.identidad.dependencies import require_roles
from app.modules.identidad.models import Usuario
from app.modules.membresias.models import Membresia
from app.modules.sedes.models import Sede
from app.modules.socios.models import Socio

router = APIRouter(tags=["clases"])


def _obtener_clase_o_404(db: Session, clase_id: uuid.UUID) -> Clase:
    clase = db.get(Clase, clase_id)
    if clase is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clase no encontrada")
    return clase


def _obtener_reserva_o_404(db: Session, reserva_id: uuid.UUID) -> Reserva:
    reserva = db.get(Reserva, reserva_id)
    if reserva is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva no encontrada")
    return reserva


def _entrenador_propio(db: Session, usuario: Usuario) -> Entrenador | None:
    return db.query(Entrenador).filter(Entrenador.usuario_id == usuario.id).first()


def _validar_entrenador_activo(db: Session, entrenador_id: uuid.UUID) -> None:
    entrenador = db.get(Entrenador, entrenador_id)
    if entrenador is None or not entrenador.activo:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="entrenador_id inválido: debe existir y estar activo",
        )


def _construir_detalle(db: Session, clase: Clase) -> ClaseDetail:
    ocupacion = service.calcular_ocupacion(db, clase)
    return ClaseDetail(
        id=clase.id,
        sede_id=clase.sede_id,
        entrenador_id=clase.entrenador_id,
        nombre=clase.nombre,
        tipo=clase.tipo,
        fecha_hora=clase.fecha_hora,
        duracion_minutos=clase.duracion_minutos,
        aforo_maximo=clase.aforo_maximo,
        recurrente=clase.recurrente,
        estado=clase.estado,
        regla_recurrencia=clase.regla_recurrencia,
        plazas_disponibles=ocupacion["plazas_disponibles"],
        en_lista_espera=ocupacion["en_lista_espera"],
    )


@router.post("/clases", response_model=ClaseDetail, status_code=status.HTTP_201_CREATED)
def crear_clase(
    body: ClaseCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede")),
):
    if usuario.rol == "gestor_sede" and usuario.sede_id != body.sede_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre esta sede")

    if db.get(Sede, body.sede_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sede no encontrada")

    _validar_entrenador_activo(db, body.entrenador_id)

    clase = service.crear_clase(db, **body.model_dump())
    return _construir_detalle(db, clase)


@router.get("/clases", response_model=list[ClaseListItem])
def listar_clases(
    sede_id: uuid.UUID | None = Query(default=None),
    fecha: date | None = Query(default=None),
    db: Session = Depends(get_db),
    # comercial excluido a propósito: no accede a datos operativos de
    # clases/aforo (specs/001 - Identidad y Roles).
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede", "entrenador", "socio")),
):
    query = db.query(Clase)
    if usuario.rol == "entrenador":
        # entrenador: solo ve sus propias clases asignadas (specs/017 FR4),
        # mismo criterio de scoping que socios/router.py para sus socios.
        entrenador = _entrenador_propio(db, usuario)
        ids_entrenador = [entrenador.id] if entrenador is not None else []
        query = query.filter(Clase.entrenador_id.in_(ids_entrenador))
    elif usuario.rol == "socio":
        # socio: el catálogo solo debe mostrar clases de su propia sede
        # (regla de negocio de specs/005); nunca clases de otras sedes,
        # ni siquiera si se solicita explícitamente vía sede_id.
        socio = db.query(Socio).filter(Socio.usuario_id == usuario.id).first()
        if socio is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Socio no encontrado para este usuario")
        query = query.filter(Clase.sede_id == socio.sede_id)
        # El catálogo del socio solo retiene histórico hasta el lunes 00:00
        # de la semana en curso (semana lunes-domingo); no afecta a admin/
        # gestor_sede/entrenador, que siguen viendo el histórico completo.
        # Esto no borra ni modifica ningún registro: es solo un filtro de
        # lectura sobre la consulta de listado.
        ahora = datetime.utcnow()
        inicio_semana_actual = datetime.combine(ahora.date() - timedelta(days=ahora.weekday()), datetime.min.time())
        query = query.filter(Clase.fecha_hora >= inicio_semana_actual)
    if sede_id is not None:
        query = query.filter(Clase.sede_id == sede_id)
    if fecha is not None:
        query = query.filter(
            Clase.fecha_hora >= datetime.combine(fecha, datetime.min.time()),
            Clase.fecha_hora < datetime.combine(fecha, datetime.max.time()),
        )
    return query.all()


@router.get("/clases/{clase_id}", response_model=ClaseDetail)
def obtener_clase(
    clase_id: uuid.UUID,
    db: Session = Depends(get_db),
    # comercial excluido a propósito: no accede a datos operativos de
    # clases/aforo (specs/001 - Identidad y Roles).
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede", "entrenador", "socio")),
):
    clase = _obtener_clase_o_404(db, clase_id)

    if usuario.rol == "entrenador":
        entrenador = _entrenador_propio(db, usuario)
        if entrenador is None or entrenador.id != clase.entrenador_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No imparte esta clase")

    if usuario.rol == "socio":
        socio = db.query(Socio).filter(Socio.usuario_id == usuario.id).first()
        if socio is None or socio.sede_id != clase.sede_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre esta clase")

    return _construir_detalle(db, clase)


@router.put("/clases/{clase_id}", response_model=ClaseDetail)
def editar_clase(
    clase_id: uuid.UUID,
    body: ClaseUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede")),
):
    clase = _obtener_clase_o_404(db, clase_id)
    if usuario.rol == "gestor_sede" and usuario.sede_id != clase.sede_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre esta clase")

    cambios = body.model_dump(exclude_unset=True)
    if "entrenador_id" in cambios:
        _validar_entrenador_activo(db, cambios["entrenador_id"])

    for campo, valor in cambios.items():
        setattr(clase, campo, valor)
    db.commit()
    db.refresh(clase)
    return _construir_detalle(db, clase)


@router.post("/clases/{clase_id}/reservar", response_model=ReservaOut, status_code=status.HTTP_201_CREATED)
def reservar_clase(
    clase_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("socio")),
):
    clase = _obtener_clase_o_404(db, clase_id)

    socio = db.query(Socio).filter(Socio.usuario_id == usuario.id).first()
    if socio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Socio no encontrado")

    if clase.sede_id != socio.sede_id:
        # Defensa en profundidad: el catálogo del portal de socio ya no
        # muestra clases de otras sedes, pero rechazamos también aquí
        # cualquier intento de reserva directa vía API sobre una clase de
        # una sede distinta a la del socio (specs/005).
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre esta clase")

    if clase.estado != "activa":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La clase no está activa")

    if clase.fecha_hora < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La clase ya ha finalizado")

    membresia_activa = (
        db.query(Membresia).filter(Membresia.socio_id == socio.id, Membresia.estado == "activa").first()
    )
    if membresia_activa is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene una membresía activa")

    ya_reservada = (
        db.query(Reserva)
        .filter(
            Reserva.clase_id == clase.id,
            Reserva.socio_id == socio.id,
            Reserva.estado.in_(("confirmada", "lista_espera")),
        )
        .first()
    )
    if ya_reservada is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya tiene una reserva para esta clase")

    return service.reservar_clase(db, clase, socio.id)


@router.get("/reservas", response_model=list[ReservaOut])
def listar_reservas(
    socio_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("socio", "gestor_sede", "admin")),
):
    # socio siempre auto-scoped a sí mismo; admin/gestor_sede pueden filtrar
    # por socio_id. Necesario para que el portal de socio (specs/015) liste
    # sus propias reservas sin conocer de antemano el reserva_id.
    if usuario.rol == "socio":
        socio = db.query(Socio).filter(Socio.usuario_id == usuario.id).first()
        if socio is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Socio no encontrado para este usuario")
        return (
            db.query(Reserva)
            .filter(Reserva.socio_id == socio.id, Reserva.estado.in_(("confirmada", "lista_espera")))
            .all()
        )

    query = db.query(Reserva).filter(Reserva.estado.in_(("confirmada", "lista_espera")))
    if socio_id is not None:
        query = query.filter(Reserva.socio_id == socio_id)
    return query.all()


@router.delete("/reservas/{reserva_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancelar_reserva(
    reserva_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("socio", "gestor_sede", "admin")),
):
    reserva = _obtener_reserva_o_404(db, reserva_id)
    clase = _obtener_clase_o_404(db, reserva.clase_id)

    if usuario.rol == "socio":
        socio = db.query(Socio).filter(Socio.usuario_id == usuario.id).first()
        if socio is None or socio.id != reserva.socio_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre esta reserva")
    elif usuario.rol == "gestor_sede" and usuario.sede_id != clase.sede_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre esta reserva")

    if reserva.estado == "cancelada":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La reserva ya está cancelada")

    # Solo restringe la cancelación de una plaza ya ocupada (reserva
    # confirmada); salir de la lista de espera no ocupa plaza y debe poder
    # hacerse en cualquier momento, incluso a <1h del inicio (specs/005).
    if reserva.estado == "confirmada":
        limite = clase.fecha_hora - timedelta(hours=service.HORAS_LIMITE_CANCELACION_CONFIRMADA)
        if datetime.utcnow() > limite:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "No se puede cancelar una reserva confirmada con menos de "
                    f"{service.HORAS_LIMITE_CANCELACION_CONFIRMADA}h de antelación"
                ),
            )

    service.cancelar_reserva(db, reserva, clase)


@router.get("/clases/{clase_id}/ocupacion", response_model=OcupacionOut)
def ver_ocupacion(
    clase_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede", "entrenador")),
):
    clase = _obtener_clase_o_404(db, clase_id)

    if usuario.rol == "gestor_sede" and usuario.sede_id != clase.sede_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre esta clase")

    if usuario.rol == "entrenador":
        entrenador = _entrenador_propio(db, usuario)
        if entrenador is None or entrenador.id != clase.entrenador_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No imparte esta clase")

    ocupacion = service.calcular_ocupacion(db, clase)
    return OcupacionOut(clase_id=clase.id, aforo_maximo=clase.aforo_maximo, **ocupacion)


@router.post("/clases/reasignar-por-baja-entrenador", response_model=list[ClaseListItem])
def reasignar_por_baja_entrenador(
    body: ReasignarPorBajaEntrenadorBody,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede")),
):
    entrenador = db.get(Entrenador, body.entrenador_id)
    if entrenador is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrenador no encontrado")

    if usuario.rol == "gestor_sede" and usuario.sede_id != entrenador.sede_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre este entrenador")

    if body.decision == "reasignar":
        _validar_entrenador_activo(db, body.nuevo_entrenador_id)
        nuevo_entrenador = db.get(Entrenador, body.nuevo_entrenador_id)
        if nuevo_entrenador.sede_id != entrenador.sede_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="nuevo_entrenador_id inválido: debe pertenecer a la misma sede que el entrenador dado de baja",
            )

    return service.reasignar_por_baja_entrenador(db, body.entrenador_id, body.decision, body.nuevo_entrenador_id)
