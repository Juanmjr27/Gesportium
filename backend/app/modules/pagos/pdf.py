from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.modules.pagos.models import Pago

# backend/storage/facturas — fuera de app/ para no mezclarse con el código
# fuente; excluido de git (ver .gitignore raíz).
STORAGE_DIR = Path(__file__).resolve().parents[3] / "storage" / "facturas"


def generar_pdf_factura(numero: str, pago: Pago) -> str:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    ruta = STORAGE_DIR / f"{numero}.pdf"

    c = canvas.Canvas(str(ruta), pagesize=A4)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 800, "Factura Gesportium")
    c.setFont("Helvetica", 11)
    c.drawString(50, 770, f"Número: {numero}")
    c.drawString(50, 750, f"Fecha de emisión: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}")
    c.drawString(50, 730, f"Concepto: {pago.concepto}")
    c.drawString(50, 710, f"Importe: {pago.importe} EUR")
    c.save()

    return str(ruta)
