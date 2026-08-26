import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.entrenadores import service as entrenadores_service
from app.modules.entrenadores.models import Entrenador, SocioAsignado
from app.modules.entrenamiento.models import EjercicioRutina, PlanNutricional, Rutina
from app.modules.entrenamiento.schemas import EjercicioOut, PlanNutricionalOut, RutinaOut
from app.modules.identidad.dependencies import require_roles
from app.modules.identidad.models import Usuario
from app.modules.membresias.models import Membresia
from app.modules.membresias.schemas import MembresiaDetail
from app.modules.sedes.models import Sede
from app.modules.socios import service
from app.modules.socios.models import DocumentoSocio, NotaSocio, Socio
from app.modules.socios.schemas import (
    CAMPOS_EDITABLES_PROPIO_SOCIO,
    CandidatoSocioOut,
    DocumentoSocioCreate,
    DocumentoSocioOut,
    EntrenadorAsignadoOut,
    NotaSocioCreate,
    NotaSocioOut,
    SocioCreate,
    SocioDetail,
    SocioFichaOut,
    SocioListItem,
    SocioSelf,
    SocioTransferir,
    SocioUpdate,
)

router = APIRouter(prefix="/socios", tags=["socios"])


def _obtener_socio_o_404(db: Session, socio_id: uuid.UUID) -> Socio:
    socio = db.get(Socio, socio_id)
    if socio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Socio no encontrado")
    return socio


def _es_propio_socio(usuario: Usuario, socio: Socio) -> bool:
    return usuario.rol == "socio" and usuario.id == socio.usuario_id


def _verificar_acceso_gestion(usuario: Usuario, socio: Socio) -> None:
    if usuario.rol == "admin":
        return
    if usuario.rol == "gestor_sede" and usuario.sede_id == socio.sede_id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre este socio")


def _construir_detalle(db: Session, socio: Socio) -> SocioDetail:
    notas = db.query(NotaSocio).filter(NotaSocio.socio_id == socio.id).order_by(NotaSocio.fecha.desc()).all()
    detalle = SocioDetail.model_validate(socio)
    detalle.notas = [NotaSocioOut.model_validate(n) for n in notas]
    return detalle


def _rutina_con_ejercicios(db: Session, rutina: Rutina) -> RutinaOut:
    ejercicios = db.query(EjercicioRutina).filter(EjercicioRutina.rutina_id == rutina.id).all()
    detalle = RutinaOut.model_validate(rutina)
    detalle.ejercicios = [EjercicioOut.model_validate(e) for e in ejercicios]
    return detalle


def _construir_ficha(db: Session, socio: Socio) -> SocioFichaOut:
    """Agrega datos ya definidos en 004 (membresías), 006 (entrenador asignado) y
    007 (rutinas/planes) sin duplicar su lógica de negocio (specs/017 FR8)."""
    membresia = db.query(Membresia).filter(Membresia.socio_id == socio.id).order_by(Membresia.fecha_inicio.desc()).first()

    asignacion = (
        db.query(SocioAsignado)
        .filter(SocioAsignado.socio_id == socio.id, SocioAsignado.fecha_fin.is_(None))
        .first()
    )
    entrenador_asignado = None
    if asignacion is not None:
        entrenador = db.get(Entrenador, asignacion.entrenador_id)
        usuario_entrenador = db.get(Usuario, entrenador.usuario_id)
        entrenador_asignado = EntrenadorAsignadoOut(
            id=entrenador.id, email=usuario_entrenador.email, especialidades=entrenador.especialidades
        )

    rutinas = db.query(Rutina).filter(Rutina.socio_id == socio.id).all()
    planes = db.query(PlanNutricional).filter(PlanNutricional.socio_id == socio.id).all()

    ficha = SocioFichaOut.model_validate(socio)
    ficha.membresia = MembresiaDetail.model_validate(membresia) if membresia else None
    ficha.entrenador_asignado = entrenador_asignado
    ficha.rutinas = [_rutina_con_ejercicios(db, r) for r in rutinas]
    ficha.planes_nutricionales = [PlanNutricionalOut.model_validate(p) for p in planes]
    return ficha


@router.post("", response_model=SocioDetail, status_code=status.HTTP_201_CREATED)
def crear_socio(
    body: SocioCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede")),
):
    if usuario.rol == "gestor_sede" and usuario.sede_id != body.sede_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre esta sede")

    if db.get(Sede, body.sede_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sede no encontrada")

    usuario_socio = db.get(Usuario, body.usuario_id)
    if usuario_socio is None or usuario_socio.rol != "socio":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="usuario_id inválido: debe existir y tener rol 'socio'")

    ya_existe = db.query(Socio).filter(Socio.usuario_id == body.usuario_id).first()
    if ya_existe is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un socio para este usuario")

    socio = service.crear_socio(db, body, autor_id=usuario.id)
    return _construir_detalle(db, socio)


@router.get("/candidatos-alta", response_model=list[CandidatoSocioOut])
def listar_candidatos_alta(
    q: str | None = Query(default=None, min_length=1),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede")),
):
    """Usuarios con rol 'socio' que aún no tienen un registro Socio asociado."""
    ids_con_socio = db.query(Socio.usuario_id)
    query = db.query(Usuario).filter(
        Usuario.rol == "socio",
        Usuario.activo.is_(True),
        Usuario.id.notin_(ids_con_socio),
    )
    if q:
        query = query.filter(Usuario.email.ilike(f"%{q}%"))
    return [CandidatoSocioOut(id=u.id, email=u.email) for u in query.order_by(Usuario.email).all()]


def _listar_con_email(query) -> list[SocioListItem]:
    filas = query.join(Usuario, Usuario.id == Socio.usuario_id).add_columns(Usuario.email).all()
    return [
        SocioListItem(
            id=socio.id,
            usuario_id=socio.usuario_id,
            email=email,
            sede_id=socio.sede_id,
            activo=socio.activo,
            fecha_alta=socio.fecha_alta,
        )
        for socio, email in filas
    ]


@router.get("", response_model=list[SocioListItem])
def listar_socios(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede", "entrenador")),
):
    if usuario.rol == "admin":
        return _listar_con_email(db.query(Socio))
    if usuario.rol == "gestor_sede":
        return _listar_con_email(db.query(Socio).filter(Socio.sede_id == usuario.sede_id))
    # entrenador: solo ve los socios que tiene asignados en entrenamiento
    # personal (módulo 006, tabla socios_asignados), no el listado completo.
    ids_asignados = entrenadores_service.ids_socios_asignados(db, usuario.id)
    return _listar_con_email(db.query(Socio).filter(Socio.id.in_(ids_asignados)))


@router.get("/me", response_model=SocioSelf)
def obtener_socio_propio(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("socio")),
):
    # Resuelve el socio_id del usuario autenticado: el JWT solo lleva
    # usuario_id/rol/sede_id, y el frontend del portal de socio (specs/015)
    # necesita descubrir su propio socio_id antes de poder llamar al resto
    # de endpoints con scope de socio (/membresias, /pagos, /accesos, etc.).
    socio = db.query(Socio).filter(Socio.usuario_id == usuario.id).first()
    if socio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Socio no encontrado para este usuario")
    return SocioSelf.model_validate(socio)


@router.get("/{socio_id}", response_model=SocioDetail | SocioSelf)
def obtener_socio(
    socio_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede", "entrenador", "socio")),
):
    socio = _obtener_socio_o_404(db, socio_id)

    if usuario.rol in ("admin", "gestor_sede"):
        _verificar_acceso_gestion(usuario, socio)
        return _construir_detalle(db, socio)

    if usuario.rol == "socio":
        if not _es_propio_socio(usuario, socio):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre este socio")
        return SocioSelf.model_validate(socio)

    # entrenador: solo puede ver el detalle de socios que tiene asignados
    # (mismo criterio que el listado, para un único comportamiento de acceso).
    if socio.id not in entrenadores_service.ids_socios_asignados(db, usuario.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre este socio")
    return SocioSelf.model_validate(socio)


@router.get("/{socio_id}/ficha", response_model=SocioFichaOut)
def obtener_ficha_socio(
    socio_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede", "entrenador")),
):
    socio = _obtener_socio_o_404(db, socio_id)

    if usuario.rol in ("admin", "gestor_sede"):
        _verificar_acceso_gestion(usuario, socio)
    elif socio.id not in entrenadores_service.ids_socios_asignados(db, usuario.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre este socio")

    return _construir_ficha(db, socio)


@router.put("/{socio_id}", response_model=SocioDetail | SocioSelf)
def editar_socio(
    socio_id: uuid.UUID,
    body: SocioUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede", "socio")),
):
    socio = _obtener_socio_o_404(db, socio_id)
    cambios = body.model_dump(exclude_unset=True)

    if usuario.rol == "socio":
        if not _es_propio_socio(usuario, socio):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre este socio")
        if not set(cambios.keys()) <= CAMPOS_EDITABLES_PROPIO_SOCIO:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo puede editar sus datos de contacto")
        for campo, valor in cambios.items():
            setattr(socio, campo, valor)
        db.commit()
        db.refresh(socio)
        return SocioSelf.model_validate(socio)

    _verificar_acceso_gestion(usuario, socio)
    for campo, valor in cambios.items():
        setattr(socio, campo, valor)
    db.commit()
    db.refresh(socio)
    return _construir_detalle(db, socio)


@router.delete("/{socio_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_socio(
    socio_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede")),
):
    socio = _obtener_socio_o_404(db, socio_id)
    _verificar_acceso_gestion(usuario, socio)

    service.dar_baja_socio(db, socio, autor_id=usuario.id)
    return None


@router.post("/{socio_id}/documentos", response_model=DocumentoSocioOut, status_code=status.HTTP_201_CREATED)
def subir_documento(
    socio_id: uuid.UUID,
    body: DocumentoSocioCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede")),
):
    socio = _obtener_socio_o_404(db, socio_id)
    _verificar_acceso_gestion(usuario, socio)

    documento = DocumentoSocio(socio_id=socio.id, **body.model_dump())
    db.add(documento)
    db.commit()
    db.refresh(documento)
    return documento


@router.post("/{socio_id}/transferir", response_model=SocioDetail)
def transferir_socio(
    socio_id: uuid.UUID,
    body: SocioTransferir,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede")),
):
    socio = _obtener_socio_o_404(db, socio_id)
    _verificar_acceso_gestion(usuario, socio)

    if body.nueva_sede_id == socio.sede_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El socio ya pertenece a esa sede")

    if db.get(Sede, body.nueva_sede_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sede no encontrada")

    socio = service.transferir_socio(db, socio, body.nueva_sede_id)
    return _construir_detalle(db, socio)


@router.post("/{socio_id}/notas", response_model=NotaSocioOut, status_code=status.HTTP_201_CREATED)
def anadir_nota(
    socio_id: uuid.UUID,
    body: NotaSocioCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede")),
):
    socio = _obtener_socio_o_404(db, socio_id)
    _verificar_acceso_gestion(usuario, socio)

    nota = NotaSocio(socio_id=socio.id, autor_id=usuario.id, contenido=body.contenido)
    db.add(nota)
    db.commit()
    db.refresh(nota)
    return nota
