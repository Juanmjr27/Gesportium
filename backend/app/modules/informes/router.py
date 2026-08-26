import uuid
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.identidad.dependencies import require_roles
from app.modules.identidad.models import Usuario
from app.modules.informes import export, service
from app.modules.informes.ollama_client import generar_resumen
from app.modules.informes.schemas import (
    TIPOS_INFORME,
    InformeComercialOut,
    InformeFinancieroOut,
    InformeOcupacionOut,
    InformeSociosOut,
)
from app.modules.sedes.models import Sede

router = APIRouter(prefix="/informes", tags=["informes"])

SCHEMAS_INFORME = {
    "socios": InformeSociosOut,
    "financiero": InformeFinancieroOut,
    "ocupacion": InformeOcupacionOut,
    "comercial": InformeComercialOut,
}

MEDIA_TYPES_EXPORTAR = {
    "pdf": "application/pdf",
    "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
EXTENSIONES_EXPORTAR = {"pdf": "pdf", "excel": "xlsx"}


def _validar_tipo(tipo: str) -> None:
    if tipo not in TIPOS_INFORME:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de informe no encontrado")


def _validar_rango_fechas(fecha_inicio: date, fecha_fin: date) -> None:
    if fecha_inicio > fecha_fin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="fecha_inicio debe ser anterior o igual a fecha_fin"
        )


def _resolver_sede(usuario: Usuario, sede_id: uuid.UUID | None, db: Session) -> uuid.UUID | None:
    if usuario.rol == "gestor_sede":
        if sede_id is not None and sede_id != usuario.sede_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre esta sede")
        return usuario.sede_id
    if sede_id is not None and db.get(Sede, sede_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sede no encontrada")
    return sede_id


@router.get("/{tipo}")
def obtener_informe(
    tipo: str,
    fecha_inicio: date,
    fecha_fin: date,
    sede_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede")),
):
    _validar_tipo(tipo)
    _validar_rango_fechas(fecha_inicio, fecha_fin)
    sede_id = _resolver_sede(usuario, sede_id, db)

    datos = service.calcular_informe(tipo, db, sede_id, fecha_inicio, fecha_fin)
    return SCHEMAS_INFORME[tipo](**datos)


@router.get("/{tipo}/exportar")
def exportar_informe(
    tipo: str,
    formato: Literal["pdf", "excel"],
    fecha_inicio: date,
    fecha_fin: date,
    sede_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede")),
):
    _validar_tipo(tipo)
    _validar_rango_fechas(fecha_inicio, fecha_fin)
    sede_id = _resolver_sede(usuario, sede_id, db)

    datos = service.calcular_informe(tipo, db, sede_id, fecha_inicio, fecha_fin)
    ruta = export.generar_pdf(tipo, datos) if formato == "pdf" else export.generar_excel(tipo, datos)

    return FileResponse(
        ruta,
        media_type=MEDIA_TYPES_EXPORTAR[formato],
        filename=f"informe-{tipo}.{EXTENSIONES_EXPORTAR[formato]}",
    )


@router.post("/{tipo}/resumen-ia")
def generar_resumen_informe(
    tipo: str,
    fecha_inicio: date,
    fecha_fin: date,
    sede_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede")),
):
    _validar_tipo(tipo)
    _validar_rango_fechas(fecha_inicio, fecha_fin)
    sede_id = _resolver_sede(usuario, sede_id, db)

    datos = service.calcular_informe(tipo, db, sede_id, fecha_inicio, fecha_fin)
    datos["resumen_ia"] = generar_resumen(tipo, datos)
    return SCHEMAS_INFORME[tipo](**datos)
