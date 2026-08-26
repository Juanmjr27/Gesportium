import unicodedata
import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.modules.entrenamiento.models import CumplimientoRutina, DIAS_SEMANA, EjercicioRutina, PlanNutricional, Rutina


def _normalizar_dia_semana(valor: str) -> str:
    """Minúsculas y sin tildes, para que 'miércoles' o 'Miércoles' casen con
    DIAS_SEMANA igual que 'miercoles'. Evita tener que listar a mano cada
    variante acentuada de cada día."""
    sin_tildes = unicodedata.normalize("NFKD", valor).encode("ascii", "ignore").decode("ascii")
    return sin_tildes.strip().lower()


def crear_rutina(db: Session, entrenador_id: uuid.UUID, socio_id: uuid.UUID, nombre: str, ejercicios: list[dict]) -> Rutina:
    rutina = Rutina(entrenador_id=entrenador_id, socio_id=socio_id, nombre=nombre, origen="manual")
    db.add(rutina)
    db.flush()

    for ejercicio in ejercicios:
        db.add(EjercicioRutina(rutina_id=rutina.id, **ejercicio))

    db.commit()
    db.refresh(rutina)
    return rutina


def crear_plan_nutricional(db: Session, entrenador_id: uuid.UUID, socio_id: uuid.UUID, nombre: str, notas: str | None) -> PlanNutricional:
    plan = PlanNutricional(entrenador_id=entrenador_id, socio_id=socio_id, nombre=nombre, notas=notas, origen="manual")
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def marcar_cumplimiento(db: Session, ejercicio_id: uuid.UUID, socio_id: uuid.UUID, fecha: date, completado: bool) -> CumplimientoRutina:
    registro = (
        db.query(CumplimientoRutina)
        .filter(
            CumplimientoRutina.ejercicio_id == ejercicio_id,
            CumplimientoRutina.socio_id == socio_id,
            CumplimientoRutina.fecha == fecha,
        )
        .first()
    )
    if registro is None:
        registro = CumplimientoRutina(ejercicio_id=ejercicio_id, socio_id=socio_id, fecha=fecha, completado=completado)
        db.add(registro)
    else:
        registro.completado = completado

    db.commit()
    db.refresh(registro)
    return registro


def _validar_contenido_rutina(contenido: dict) -> tuple[str, list[dict]]:
    try:
        nombre = contenido["nombre"]
        ejercicios_raw = contenido["ejercicios"]
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValueError("nombre inválido")
        if not isinstance(ejercicios_raw, list) or len(ejercicios_raw) == 0:
            raise ValueError("ejercicios inválido: se esperaba una lista no vacía")

        ejercicios = []
        for ejercicio_raw in ejercicios_raw:
            dia_semana_raw = str(ejercicio_raw["dia_semana"])
            dia_semana = _normalizar_dia_semana(dia_semana_raw)
            if dia_semana not in DIAS_SEMANA:
                raise ValueError(f"dia_semana inválido: {dia_semana_raw}")
            ejercicios.append(
                {
                    "nombre": str(ejercicio_raw["nombre"]),
                    "series": int(ejercicio_raw["series"]),
                    "repeticiones": int(ejercicio_raw["repeticiones"]),
                    "dia_semana": dia_semana,
                    "descanso_segundos": int(ejercicio_raw["descanso_segundos"]),
                }
            )
        return nombre, ejercicios
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Contenido de borrador inválido para rutina: {exc}") from exc


def crear_rutina_desde_borrador(
    db: Session, entrenador_id: uuid.UUID, socio_id: uuid.UUID, borrador_id: uuid.UUID, contenido: dict
) -> Rutina:
    """Punto de integración sancionado para el módulo 016 (plan.md Fase 2):
    mapea `borradores_ia.contenido` a Rutina/EjercicioRutina tras la
    aprobación humana del entrenador. Lanza ValueError si el contenido no
    tiene el formato esperado, para que el módulo 016 rechace la aprobación
    en vez de crear un registro incompleto.
    """
    nombre, ejercicios = _validar_contenido_rutina(contenido)

    rutina = Rutina(entrenador_id=entrenador_id, socio_id=socio_id, nombre=nombre, origen="ia", borrador_id=borrador_id)
    db.add(rutina)
    db.flush()

    for ejercicio in ejercicios:
        db.add(EjercicioRutina(rutina_id=rutina.id, **ejercicio))

    db.commit()
    db.refresh(rutina)
    return rutina


def _validar_contenido_plan_nutricional(contenido: dict) -> tuple[str, str | None]:
    try:
        nombre = contenido["nombre"]
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValueError("nombre inválido")
        notas = contenido.get("notas")
        if notas is not None and not isinstance(notas, str):
            raise ValueError("notas inválido: se esperaba texto")
        return nombre, notas
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Contenido de borrador inválido para plan nutricional: {exc}") from exc


def crear_plan_nutricional_desde_borrador(
    db: Session, entrenador_id: uuid.UUID, socio_id: uuid.UUID, borrador_id: uuid.UUID, contenido: dict
) -> PlanNutricional:
    """Equivalente a crear_rutina_desde_borrador para planes nutricionales."""
    nombre, notas = _validar_contenido_plan_nutricional(contenido)

    plan = PlanNutricional(entrenador_id=entrenador_id, socio_id=socio_id, nombre=nombre, notas=notas, origen="ia", borrador_id=borrador_id)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan
