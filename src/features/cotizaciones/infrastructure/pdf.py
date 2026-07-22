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
            buffer, pagesize=A4, title=f"Cotización #{cotizacion.numero}"
        )
        styles = getSampleStyleSheet()
        elementos = []

        elementos.append(Paragraph("VisionPrice — Cotización", styles["Title"]))
        elementos.append(
            Paragraph(
                f"Cotización #{cotizacion.numero} &nbsp;·&nbsp; "
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

    def render_proyecto(self, cotizaciones: list[Cotizacion], proyecto_id: int, info_proyecto=None) -> bytes:
        from collections import defaultdict
        from datetime import datetime

        buffer = BytesIO()
        
        titulo_doc = f"Proyecto #{proyecto_id} - Cotizaciones"
        if info_proyecto:
            titulo_doc = f"{info_proyecto.nombre_proyecto} - Lista de Compras"
            
        doc = SimpleDocTemplate(
            buffer, pagesize=A4, title=titulo_doc
        )
        styles = getSampleStyleSheet()
        elementos = []

        # Título principal
        titulo = "Lista de Compras"
        if info_proyecto:
            titulo = f"Lista de Compras — {info_proyecto.nombre_proyecto}"
        else:
            titulo = f"Lista de Compras — Proyecto #{proyecto_id}"
            
        elementos.append(Paragraph(titulo, styles["Title"]))
        
        # Subtítulo / Encabezado
        if info_proyecto:
            fecha_hoy = datetime.now().strftime("%Y-%m-%d")
            dir_str = f" &nbsp;·&nbsp; {info_proyecto.direccion}" if info_proyecto.direccion else ""
            subtitulo = (
                f"Generado el: {fecha_hoy} &nbsp;·&nbsp; "
                f"Por: {info_proyecto.nombre_usuario}{dir_str}"
            )
            elementos.append(Paragraph(subtitulo, styles["Normal"]))
            elementos.append(Spacer(1, 0.4 * cm))
        
        # Agrupar lineas por proveedor
        lineas_por_proveedor = defaultdict(list)
        gran_total = 0.0

        for c in cotizaciones:
            for ln in c.lineas:
                proveedor = ln.proveedor_nombre or "Sin Proveedor"
                # Incluir la distancia si existe
                dist_str = f" ({ln.proveedor_distancia:.1f} km)" if ln.proveedor_distancia else ""
                llave_proveedor = f"{proveedor}{dist_str}"
                
                lineas_por_proveedor[llave_proveedor].append(ln)
                gran_total += ln.subtotal

        # Ordenar proveedores (opcional)
        for prov_nombre, lineas in sorted(lineas_por_proveedor.items()):
            elementos.append(Paragraph(prov_nombre, styles["Heading2"]))
            
            filas = [["Descripción", "Cant.", "Unidad", "P. unitario", "Subtotal"]]
            subtotal_prov = 0.0
            
            for ln in lineas:
                filas.append([
                    ln.descripcion,
                    f"{ln.cantidad:g}",
                    ln.unidad,
                    f"${ln.precio_unitario:,.2f}",
                    f"${ln.subtotal:,.2f}",
                ])
                subtotal_prov += ln.subtotal
                
            filas.append(["", "", "", "Subtotal Prov.", f"${subtotal_prov:,.2f}"])
            
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
            elementos.append(Spacer(1, 0.4 * cm))

        # Gran total
        elementos.append(Spacer(1, 0.8 * cm))
        elementos.append(Paragraph(f"TOTAL GENERAL: ${gran_total:,.2f}", styles["Heading1"]))
        
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
