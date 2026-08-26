import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.identidad.dependencies import require_roles
from app.modules.identidad.models import Usuario
from app.modules.membresias import service
from app.modules.membresias.models import Membresia, PlanMembresia
from app.modules.membresias.schemas import (
    CancelarMembresiaBody,
    CongelarMembresiaBody,
    MembresiaCreate,
    MembresiaDetail,
    PlanMembresiaCreate,
    PlanMembresiaOut,
    PlanMembresiaUpdate,
)
from app.modules.socios import service as socios_service

router = APIRouter(tags=["membresias"])


def _obtener_plan_o_404(db: Session, plan_id: uuid.UUID) -> PlanMembresia:
    plan = db.get(PlanMembresia, plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan de membresía no encontrado")
    return plan


def _obtener_membresia_o_404(db: Session, membresia_id: uuid.UUID) -> Membresia:
    membresia = db.get(Membresia, membresia_id)
    if membresia is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membresía no encontrada")
    return membresia


def _verificar_acceso_membresia(db: Session, usuario: Usuario, membresia: Membresia):
    socio = socios_service.obtener_socio(db, membresia.socio_id)
    if usuario.rol == "admin":
        return socio
    if usuario.rol == "gestor_sede" and usuario.sede_id == socio.sede_id:
        return socio
    if usuario.rol == "socio" and usuario.id == socio.usuario_id:
        return socio
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre esta membresía")


@router.post("/planes-membresia", response_model=PlanMembresiaOut, status_code=status.HTTP_201_CREATED)
def crear_plan(
    body: PlanMembresiaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin")),
):
    plan = PlanMembresia(**body.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.get("/planes-membresia", response_model=list[PlanMembresiaOut])
def listar_planes_publico(db: Session = Depends(get_db)):
    # Público por diseño (plan.md Fase 1): el catálogo de planes se muestra
    # en el portal sin necesidad de sesión, igual que sedes.listar_sedes_publico.
    return db.query(PlanMembresia).filter(PlanMembresia.activo.is_(True)).all()


@router.put("/planes-membresia/{plan_id}", response_model=PlanMembresiaOut)
def editar_plan(
    plan_id: uuid.UUID,
    body: PlanMembresiaUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin")),
):
    plan = _obtener_plan_o_404(db, plan_id)
    for campo, valor in body.model_dump(exclude_unset=True).items():
        setattr(plan, campo, valor)
    db.commit()
    db.refresh(plan)
    return plan


@router.post("/membresias", response_model=MembresiaDetail, status_code=status.HTTP_201_CREATED)
def crear_membresia(
    body: MembresiaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede")),
):
    socio = socios_service.obtener_socio(db, body.socio_id)
    if socio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Socio no encontrado")

    if usuario.rol == "gestor_sede" and usuario.sede_id != socio.sede_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre este socio")

    plan = _obtener_plan_o_404(db, body.plan_id)
    if not plan.activo:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El plan de membresía no está activo")

    membresia = service.crear_membresia(
        db,
        socio_id=socio.id,
        plan=plan,
        fecha_inicio=body.fecha_inicio or date.today(),
        renovacion_automatica=body.renovacion_automatica,
        autor_id=usuario.id,
    )
    return membresia


@router.get("/membresias", response_model=list[MembresiaDetail])
def listar_membresias(
    socio_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede", "socio")),
):
    # El rol socio siempre queda auto-scoped a su propio socio_id (no puede
    # pasar el query param para ver membresías ajenas); admin/gestor_sede
    # pueden filtrar opcionalmente por socio_id. Necesario para que el
    # portal de socio (specs/015) descubra su membresía activa sin conocer
    # de antemano el membresia_id.
    if usuario.rol == "socio":
        socio = socios_service.obtener_socio_por_usuario(db, usuario.id)
        if socio is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Socio no encontrado para este usuario")
        return db.query(Membresia).filter(Membresia.socio_id == socio.id).all()

    query = db.query(Membresia)
    if socio_id is not None:
        socio = socios_service.obtener_socio(db, socio_id)
        if socio is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Socio no encontrado")
        if usuario.rol == "gestor_sede" and usuario.sede_id != socio.sede_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre este socio")
        query = query.filter(Membresia.socio_id == socio_id)
    elif usuario.rol == "gestor_sede":
        ids_socios = socios_service.ids_socios_por_sede(db, usuario.sede_id)
        query = query.filter(Membresia.socio_id.in_(ids_socios))

    return query.all()


@router.get("/membresias/{membresia_id}", response_model=MembresiaDetail)
def obtener_membresia(
    membresia_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede", "socio")),
):
    membresia = _obtener_membresia_o_404(db, membresia_id)
    _verificar_acceso_membresia(db, usuario, membresia)
    return membresia


@router.post("/membresias/{membresia_id}/congelar", response_model=MembresiaDetail)
def congelar_membresia(
    membresia_id: uuid.UUID,
    body: CongelarMembresiaBody,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede", "socio")),
):
    membresia = _obtener_membresia_o_404(db, membresia_id)
    _verificar_acceso_membresia(db, usuario, membresia)

    if membresia.estado != "activa":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Solo se puede congelar una membresía activa")

    # Origen siempre "manual" en este endpoint: origen="impago" solo puede
    # producirse a través de service.congelar_por_impago, invocado por el
    # módulo 008 (contrato interno, ver plan.md Fase 2)
    return service.congelar_membresia(db, membresia, origen="manual", autor_id=usuario.id, motivo=body.motivo)


@router.post("/membresias/{membresia_id}/reactivar", response_model=MembresiaDetail)
def reactivar_membresia(
    membresia_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede", "socio")),
):
    membresia = _obtener_membresia_o_404(db, membresia_id)
    _verificar_acceso_membresia(db, usuario, membresia)

    if membresia.estado != "congelada":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Solo se puede reactivar una membresía congelada")

    try:
        return service.reactivar_membresia(db, membresia, autor_id=usuario.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post("/membresias/{membresia_id}/cancelar", response_model=MembresiaDetail)
def cancelar_membresia(
    membresia_id: uuid.UUID,
    body: CancelarMembresiaBody,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede", "socio")),
):
    membresia = _obtener_membresia_o_404(db, membresia_id)
    _verificar_acceso_membresia(db, usuario, membresia)

    if membresia.estado == "cancelada":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La membresía ya está cancelada")

    plan = _obtener_plan_o_404(db, membresia.plan_id)
    try:
        return service.cancelar_membresia(db, membresia, plan, autor_id=usuario.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
