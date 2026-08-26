import textwrap
import uuid
from pathlib import Path

from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# backend/storage/informes — fuera de app/ (mismo criterio que pagos/pdf.py),
# excluido de git vía backend/storage/ en .gitignore raíz.
STORAGE_DIR = Path(__file__).resolve().parents[3] / "storage" / "informes"

TITULOS_INFORME = {
    "socios": "Informe de socios",
    "financiero": "Informe financiero",
    "ocupacion": "Informe de ocupación de clases",
    "comercial": "Informe de rendimiento comercial",
}

RESUMENES_INFORME = {
    "socios": lambda d: [
        f"Altas: {d['total_altas']}",
        f"Bajas: {d['total_bajas']}",
        f"Socios activos al cierre: {d['socios_activos_al_cierre']}",
    ],
    "financiero": lambda d: [
        f"Ingresos: {d['total_ingresos']} EUR",
        f"Impagos: {d['total_impagos']} EUR",
    ],
    "ocupacion": lambda d: [f"Ocupación media: {d['ocupacion_media_pct']}%"],
    "comercial": lambda d: [
        f"Leads totales: {d['total_leads']}",
        f"Convertidos: {d['convertidos']}",
        f"Tasa de conversión: {d['tasa_conversion_pct']}%",
    ],
}


def _nombre_archivo(tipo: str) -> str:
    return f"{tipo}-{uuid.uuid4().hex[:8]}"


def generar_pdf(tipo: str, datos: dict) -> str:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    ruta = STORAGE_DIR / f"{_nombre_archivo(tipo)}.pdf"

    c = canvas.Canvas(str(ruta), pagesize=A4)
    y = 800
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, TITULOS_INFORME[tipo])
    y -= 25
    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Periodo: {datos['fecha_inicio']} a {datos['fecha_fin']}")
    y -= 30

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Resumen")
    y -= 20
    c.setFont("Helvetica", 11)
    for linea in RESUMENES_INFORME[tipo](datos):
        c.drawString(50, y, linea)
        y -= 18

    if datos.get("resumen_ia"):
        y -= 12
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Resumen IA")
        y -= 20
        c.setFont("Helvetica", 10)
        for linea in textwrap.wrap(datos["resumen_ia"], width=95):
            if y < 50:
                c.showPage()
                y = 800
                c.setFont("Helvetica", 10)
            c.drawString(50, y, linea)
            y -= 14

    c.save()
    return str(ruta)


def generar_excel(tipo: str, datos: dict) -> str:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    ruta = STORAGE_DIR / f"{_nombre_archivo(tipo)}.xlsx"

    wb = Workbook()
    resumen_sheet = wb.active
    resumen_sheet.title = "Resumen"
    resumen_sheet.append([TITULOS_INFORME[tipo]])
    resumen_sheet.append([f"Periodo: {datos['fecha_inicio']} a {datos['fecha_fin']}"])
    resumen_sheet.append([])
    for linea in RESUMENES_INFORME[tipo](datos):
        resumen_sheet.append([linea])
    if datos.get("resumen_ia"):
        resumen_sheet.append([])
        resumen_sheet.append(["Resumen IA"])
        resumen_sheet.append([datos["resumen_ia"]])

    detalle = datos.get("detalle", [])
    detalle_sheet = wb.create_sheet("Detalle")
    if detalle:
        columnas = list(detalle[0].keys())
        detalle_sheet.append(columnas)
        for fila in detalle:
            detalle_sheet.append([str(fila[col]) for col in columnas])

    wb.save(str(ruta))
    return str(ruta)
