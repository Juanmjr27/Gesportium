import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.entrenadores.models import Entrenador, SocioAsignado
from app.modules.entrenamiento import service
from app.modules.entrenamiento.models import (
    CumplimientoRutina,
    EjercicioRutina,
    PlanNutricional,
    Rutina,
)
from app.modules.entrenamiento.schemas import (
    CompletarEjercicioBody,
    CumplimientoOut,
    EjercicioOut,
    PlanNutricionalCreate,
    PlanNutricionalOut,
    PlanNutricionalUpdate,
    RutinaCreate,
    RutinaOut,
    RutinaUpdate,
)
from app.modules.identidad.dependencies import require_roles
from app.modules.identidad.models import Usuario
from app.modules.socios.models import Socio

router = APIRouter(tags=["entrenamiento"])


def _obtener_entrenador_propio(db: Session, usuario: Usuario) -> Entrenador:
    entrenador = db.query(Entrenador).filter(Entrenador.usuario_id == usuario.id).first()
    if entrenador is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrenador no encontrado")
    if not entrenador.activo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="El entrenador está dado de baja")
    return entrenador


def _obtener_socio_propio(db: Session, usuario: Usuario) -> Socio:
    socio = db.query(Socio).filter(Socio.usuario_id == usuario.id).first()
    if socio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Socio no encontrado")
    return socio


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


def _construir_rutina_out(db: Session, rutina: Rutina) -> RutinaOut:
    ejercicios = db.query(EjercicioRutina).filter(EjercicioRutina.rutina_id == rutina.id).all()
    detalle = RutinaOut.model_validate(rutina)
    detalle.ejercicios = [EjercicioOut.model_validate(e) for e in ejercicios]
    return detalle


@router.post("/rutinas", response_model=RutinaOut, status_code=status.HTTP_201_CREATED)
def crear_rutina(
    body: RutinaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("entrenador")),
):
    entrenador = _obtener_entrenador_propio(db, usuario)

    socio = db.get(Socio, body.socio_id)
    if socio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Socio no encontrado")

    _validar_asignacion(db, entrenador.id, socio.id)

    rutina = service.crear_rutina(db, entrenador.id, socio.id, body.nombre, [e.model_dump() for e in body.ejercicios])
    return _construir_rutina_out(db, rutina)


@router.get("/rutinas/{socio_id}", response_model=list[RutinaOut])
def ver_rutinas(
    socio_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("entrenador", "socio")),
):
    if usuario.rol == "entrenador":
        entrenador = _obtener_entrenador_propio(db, usuario)
        _validar_asignacion(db, entrenador.id, socio_id)
        rutinas = db.query(Rutina).filter(Rutina.socio_id == socio_id, Rutina.entrenador_id == entrenador.id).all()
    else:
        socio = _obtener_socio_propio(db, usuario)
        if socio.id != socio_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre estas rutinas")
        rutinas = db.query(Rutina).filter(Rutina.socio_id == socio.id).all()

    return [_construir_rutina_out(db, r) for r in rutinas]


@router.put("/rutinas/{rutina_id}", response_model=RutinaOut)
def editar_rutina(
    rutina_id: uuid.UUID,
    body: RutinaUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("entrenador")),
):
    entrenador = _obtener_entrenador_propio(db, usuario)
    rutina = db.get(Rutina, rutina_id)
    if rutina is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rutina no encontrada")
    if rutina.entrenador_id != entrenador.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre esta rutina")
    if not rutina.activa:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No se puede editar una rutina archivada")

    for campo, valor in body.model_dump(exclude_unset=True).items():
        setattr(rutina, campo, valor)
    db.commit()
    db.refresh(rutina)
    return _construir_rutina_out(db, rutina)


@router.post("/planes-nutricionales", response_model=PlanNutricionalOut, status_code=status.HTTP_201_CREATED)
def crear_plan_nutricional(
    body: PlanNutricionalCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("entrenador")),
):
    entrenador = _obtener_entrenador_propio(db, usuario)

    socio = db.get(Socio, body.socio_id)
    if socio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Socio no encontrado")

    _validar_asignacion(db, entrenador.id, socio.id)

    return service.crear_plan_nutricional(db, entrenador.id, socio.id, body.nombre, body.notas)


@router.get("/planes-nutricionales/{socio_id}", response_model=list[PlanNutricionalOut])
def ver_planes_nutricionales(
    socio_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("entrenador", "socio")),
):
    if usuario.rol == "entrenador":
        entrenador = _obtener_entrenador_propio(db, usuario)
        _validar_asignacion(db, entrenador.id, socio_id)
        return (
            db.query(PlanNutricional)
            .filter(PlanNutricional.socio_id == socio_id, PlanNutricional.entrenador_id == entrenador.id)
            .all()
        )

    socio = _obtener_socio_propio(db, usuario)
    if socio.id != socio_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre estos planes")
    return db.query(PlanNutricional).filter(PlanNutricional.socio_id == socio.id).all()


@router.put("/planes-nutricionales/{plan_id}", response_model=PlanNutricionalOut)
def editar_plan_nutricional(
    plan_id: uuid.UUID,
    body: PlanNutricionalUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("entrenador")),
):
    entrenador = _obtener_entrenador_propio(db, usuario)
    plan = db.get(PlanNutricional, plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan nutricional no encontrado")
    if plan.entrenador_id != entrenador.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre este plan")
    if not plan.activo:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No se puede editar un plan archivado")

    for campo, valor in body.model_dump(exclude_unset=True).items():
        setattr(plan, campo, valor)
    db.commit()
    db.refresh(plan)
    return plan


@router.post("/rutinas/{rutina_id}/completar", response_model=CumplimientoOut, status_code=status.HTTP_201_CREATED)
def completar_ejercicio(
    rutina_id: uuid.UUID,
    body: CompletarEjercicioBody,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("socio")),
):
    socio = _obtener_socio_propio(db, usuario)

    rutina = db.get(Rutina, rutina_id)
    if rutina is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rutina no encontrada")
    if rutina.socio_id != socio.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre esta rutina")

    ejercicio = db.get(EjercicioRutina, body.ejercicio_id)
    if ejercicio is None or ejercicio.rutina_id != rutina.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ejercicio no encontrado en esta rutina")

    return service.marcar_cumplimiento(db, ejercicio.id, socio.id, body.fecha, body.completado)


@router.get("/rutinas/{rutina_id}/cumplimiento", response_model=list[CumplimientoOut])
def ver_cumplimiento(
    rutina_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("entrenador")),
):
    entrenador = _obtener_entrenador_propio(db, usuario)
    rutina = db.get(Rutina, rutina_id)
    if rutina is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rutina no encontrada")
    if rutina.entrenador_id != entrenador.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre esta rutina")

    ejercicio_ids = [row[0] for row in db.query(EjercicioRutina.id).filter(EjercicioRutina.rutina_id == rutina.id).all()]
    return db.query(CumplimientoRutina).filter(CumplimientoRutina.ejercicio_id.in_(ejercicio_ids)).all()
