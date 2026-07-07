"""Caso de uso: crear la cotización.

El usuario elige productos cercanos y a qué superficie aplican (piso/pared).
La API recalcula precios consultando al micro de Proveedores por ID (integridad)
y convierte m² → cantidad con el rendimiento de cada producto:

    cantidad = ceil(area_m2 / rendimiento_m2)
    subtotal = cantidad × precio_unitario
"""
from dataclasses import dataclass

from src.features.cotizaciones.domain.entities import (
    Cotizacion,
    LineaCotizacion,
)
from src.features.cotizaciones.domain.motor_materiales import calcular_material
from src.features.cotizaciones.domain.ports import (
    CotizacionRepository,
    ProveedoresPort,
)
from src.shared.errors import ValidationError


@dataclass
class ItemSeleccionado:
    producto_id: int
    # Una de las dos formas de indicar el área de la superficie:
    #   - area_m2: superficie explícita (soporta N superficies del ML)
    #   - aplicar_a: atajo "piso"/"pared" que toma piso_m2/paredes_m2 del comando
    area_m2: float | None = None
    aplicar_a: str | None = None
    descripcion: str | None = None  # etiqueta de la superficie (ej. "piso sala")


@dataclass
class CrearCotizacionCommand:
    proyecto_id: int
    usuario_id: int
    piso_m2: float | None
    paredes_m2: float | None
    items: list[ItemSeleccionado]


class CrearCotizacion:
    def __init__(
        self,
        repo: CotizacionRepository,
        proveedores: ProveedoresPort,
        merma: float = 0.08,
    ) -> None:
        self._repo = repo
        self._proveedores = proveedores
        self._merma = merma

    async def execute(self, cmd: CrearCotizacionCommand) -> Cotizacion:
        if not cmd.items:
            raise ValidationError("La cotización no tiene productos.")

        # Precios/atributos frescos desde el micro de Proveedores.
        ids = [it.producto_id for it in cmd.items]
        productos = {p.producto_id: p for p in await self._proveedores.productos_por_ids(ids)}

        lineas: list[LineaCotizacion] = []
        for item in cmd.items:
            prod = productos.get(item.producto_id)
            if prod is None:
                raise ValidationError(
                    f"Producto {item.producto_id} no disponible en proveedores."
                )

            area = (
                item.area_m2
                if item.area_m2 is not None
                else self._area_para(item.aplicar_a, cmd)
            )
            calc = calcular_material(area, prod, merma=self._merma)
            subtotal = round(calc.cantidad * prod.precio_unitario, 2)
            etiqueta = item.descripcion or item.aplicar_a or "superficie"

            lineas.append(
                LineaCotizacion(
                    material_id=prod.producto_id,
                    proveedor_id=prod.proveedor_id,
                    descripcion=f"{prod.nombre} ({etiqueta}) — {calc.detalle}",
                    cantidad=calc.cantidad,
                    unidad=calc.unidad,
                    precio_unitario=prod.precio_unitario,
                    subtotal=subtotal,
                    piezas=calc.piezas,
                    area_m2=area,
                )
            )

        total = round(sum(l.subtotal for l in lineas), 2)
        return await self._repo.crear(
            proyecto_id=cmd.proyecto_id,
            usuario_id=cmd.usuario_id,
            total=total,
            lineas=lineas,
        )

    @staticmethod
    def _area_para(aplicar_a: str | None, cmd: CrearCotizacionCommand) -> float:
        if aplicar_a == "piso":
            if not cmd.piso_m2:
                raise ValidationError("Falta piso_m2 para un producto de piso.")
            return cmd.piso_m2
        if aplicar_a == "pared":
            if not cmd.paredes_m2:
                raise ValidationError("Falta paredes_m2 para un producto de pared.")
            return cmd.paredes_m2
        raise ValidationError(
            "Cada ítem necesita 'area_m2' o 'aplicar_a' (piso|pared)."
        )
