import uuid

from pydantic import BaseModel


class KPIComparativa(BaseModel):
    valor: float
    valor_periodo_anterior: float
    variacion_pct: float | None


class DashboardKPIsOut(BaseModel):
    sede_id: uuid.UUID | None
    socios_activos: KPIComparativa
    altas_mes: KPIComparativa
    bajas_mes: KPIComparativa
    ingresos_mes: KPIComparativa
    ocupacion_media_clases: KPIComparativa
    tasa_conversion_leads: KPIComparativa
