"""Renderer de PDF de la cotización con reportlab (en memoria)."""
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.features.cotizaciones.domain.entities import Cotizacion
from src.features.cotizaciones.domain.ports import PdfRenderer


class ReportLabPdfRenderer(PdfRenderer):
    def render(self, cotizacion: Cotizacion, *, proyecto: str | None = None) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4, title=f"Cotización #{cotizacion.id}"
        )
        styles = getSampleStyleSheet()
        elementos = []

        elementos.append(Paragraph("VisionPrice — Cotización", styles["Title"]))
        elementos.append(
            Paragraph(
                f"Cotización #{cotizacion.id} &nbsp;·&nbsp; "
                f"Proyecto {proyecto or cotizacion.proyecto_id} &nbsp;·&nbsp; "
                f"{cotizacion.fecha:%Y-%m-%d}",
                styles["Normal"],
            )
        )
        elementos.append(Spacer(1, 0.6 * cm))

        filas = [["Descripción", "Cant.", "Unidad", "P. unitario", "Subtotal"]]
        for ln in cotizacion.lineas:
            filas.append(
                [
                    ln.descripcion,
                    f"{ln.cantidad:g}",
                    ln.unidad,
                    f"${ln.precio_unitario:,.2f}",
                    f"${ln.subtotal:,.2f}",
                ]
            )
        filas.append(["", "", "", "TOTAL", f"${cotizacion.total:,.2f}"])

        tabla = Table(filas, colWidths=[7 * cm, 2 * cm, 2.5 * cm, 3 * cm, 3 * cm])
        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("GRID", (0, 0), (-1, -2), 0.5, colors.grey),
                    ("LINEABOVE", (0, -1), (-1, -1), 1, colors.black),
                    ("FONTNAME", (-2, -1), (-1, -1), "Helvetica-Bold"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f2f2f2")]),
                ]
            )
        )
        elementos.append(tabla)
        elementos.append(Spacer(1, 0.8 * cm))
        elementos.append(
            Paragraph(
                "Precios de referencia de proveedores cercanos. Sujetos a "
                "disponibilidad y cambios.",
                styles["Italic"],
            )
        )

        doc.build(elementos)
        return buffer.getvalue()
