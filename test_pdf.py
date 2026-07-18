from datetime import datetime
import os

from src.features.cotizaciones.domain.entities import Cotizacion, LineaCotizacion, InfoProyectoPdf
from src.features.cotizaciones.infrastructure.pdf import ReportLabPdfRenderer

def test_render_proyecto():
    # Mock data for Enfoque B testing
    info = InfoProyectoPdf(
        proyecto_id=1,
        nombre_proyecto="Remodelación Sala",
        direccion="Av. Siempre Viva 742",
        nombre_usuario="Juan Pérez"
    )

    # Cotizacion 1: Piso
    c1_lineas = [
        LineaCotizacion(
            material_id="m1",
            proveedor_id="p1",
            proveedor_nombre="Ferretería La Tuerca",
            proveedor_distancia=2.5,
            descripcion="Piso cerámico 60x60 (Piso sala) — 10 cajas para 15 m²",
            cantidad=10,
            unidad="caja",
            precio_unitario=250.00,
            subtotal=2500.00,
            piezas=45,
            area_m2=15.0
        ),
        LineaCotizacion(
            material_id="m2",
            proveedor_id="p1",
            proveedor_nombre="Ferretería La Tuerca",
            proveedor_distancia=2.5,
            descripcion="Pegazulejo (Piso sala) — 4 sacos para 15 m²",
            cantidad=4,
            unidad="saco",
            precio_unitario=150.00,
            subtotal=600.00,
            piezas=None,
            area_m2=15.0
        ),
        LineaCotizacion(
            material_id="m3",
            proveedor_id="p2",
            proveedor_nombre="Comex",
            proveedor_distancia=1.3,
            descripcion="Brocha 4 pulgadas",
            cantidad=2,
            unidad="pieza",
            precio_unitario=45.00,
            subtotal=90.00,
            piezas=None,
            area_m2=None
        )
    ]
    c1 = Cotizacion(
        id=12,
        proyecto_id=1,
        usuario_id=1,
        estado="confirmado",
        total=3190.00,
        fecha=datetime.now(),
        lineas=c1_lineas
    )

    # Cotizacion 2: Pintura
    c2_lineas = [
        LineaCotizacion(
            material_id="m4",
            proveedor_id="p2",
            proveedor_nombre="Comex",
            proveedor_distancia=1.3,
            descripcion="Pintura Vinimex (Paredes) — 2 cubetas",
            cantidad=2,
            unidad="cubeta",
            precio_unitario=1200.00,
            subtotal=2400.00,
            piezas=None,
            area_m2=40.0
        ),
        LineaCotizacion(
            material_id="m5",
            proveedor_id="p3", # Another provider without distance
            proveedor_nombre="Home Depot",
            proveedor_distancia=None,
            descripcion="Rodillo profesional",
            cantidad=1,
            unidad="pieza",
            precio_unitario=180.00,
            subtotal=180.00,
            piezas=None,
            area_m2=None
        )
    ]
    c2 = Cotizacion(
        id=13,
        proyecto_id=1,
        usuario_id=1,
        estado="borrador",
        total=2580.00,
        fecha=datetime.now(),
        lineas=c2_lineas
    )

    # Generate PDF
    renderer = ReportLabPdfRenderer()
    pdf_bytes = renderer.render_proyecto([c1, c2], proyecto_id=1, info_proyecto=info)

    # Save to disk
    out_path = "test_proyecto.pdf"
    with open(out_path, "wb") as f:
        f.write(pdf_bytes)
    
    print(f"Test exitoso. PDF generado y guardado en {os.path.abspath(out_path)}")

if __name__ == "__main__":
    test_render_proyecto()
