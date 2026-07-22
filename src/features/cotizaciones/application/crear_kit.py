"""Caso de uso: crear una cotización tipo KIT de instalación.

Por cada superficie, el usuario elige un producto PRINCIPAL (loseta) y,
opcionalmente, sus complementos (adhesivo, cruceta, boquilla). El back calcula
cada uno con el motor de instalación y arma N líneas por superficie.
"""
import math
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from src.features.cotizaciones.domain.entities import Cotizacion, LineaCotizacion
from src.features.cotizaciones.domain.motor_instalacion import (
    CRUCETAS_POR_PIEZA,
    crucetas_necesarias,
    paquetes,
    piezas_necesarias,
    unidades_por_rendimiento,
)
from src.features.cotizaciones.domain.ports import (
    CotizacionRepository,
    ProveedoresPort,
)
from src.shared.errors import Forbidden, ValidationError
from src.shared.proyecto_acceso import puede_acceder as _puede_acceder


@dataclass
class SuperficieKit:
    area_m2: float
    principal_producto_id: str
    descripcion: str | None = None
    metodo_crucetas: str = "tradicional"
    adhesivo_producto_id: str | None = None
    cruceta_producto_id: str | None = None
    boquilla_producto_id: str | None = None


@dataclass
class CrearKitCommand:
    proyecto_id: int
    usuario_id: int
    superficies: list[SuperficieKit]
    mano_obra: float | None = None


class CrearCotizacionKit:
    def __init__(
        self,
        repo: CotizacionRepository,
        proveedores: ProveedoresPort,
        session: AsyncSession,
        merma: float = 0.0,
    ) -> None:
        self._repo = repo
        self._proveedores = proveedores
        self._session = session
        self._merma = merma

    async def execute(self, cmd: CrearKitCommand) -> Cotizacion:
        # Verificar acceso: dueño O colaborador.
        if not await _puede_acceder(self._session, cmd.proyecto_id, cmd.usuario_id):
            raise Forbidden("No tienes acceso a este proyecto.")

        if not cmd.superficies:
            raise ValidationError("La cotización no tiene superficies.")

        # Un solo fetch al micro con todos los productos elegidos.
        ids: set[str] = set()
        for s in cmd.superficies:
            ids.add(s.principal_producto_id)
            for cid in (
                s.adhesivo_producto_id,
                s.cruceta_producto_id,
                s.boquilla_producto_id,
            ):
                if cid:
                    ids.add(cid)
        prods = {
            p.producto_id: p
            for p in await self._proveedores.productos_por_ids(list(ids))
        }

        lineas: list[LineaCotizacion] = []
        for s in cmd.superficies:
            etiqueta = s.descripcion or "superficie"
            tile = self._req(prods, s.principal_producto_id, "principal")

            # Piezas (para crucetas) si la loseta trae dimensiones.
            piezas = None
            if tile.pieza_largo_m and tile.pieza_ancho_m:
                piezas = piezas_necesarias(
                    s.area_m2, tile.pieza_largo_m, tile.pieza_ancho_m,
                    merma=self._merma,
                )

            # Cajas: por rendimiento (m²/caja) o, si no hay, agrupando las
            # piezas en cajas de piezas_por_paquete (nunca piezas sueltas:
            # el precio_unitario es por caja, no por pieza).
            if tile.rendimiento_m2:
                cant = unidades_por_rendimiento(
                    s.area_m2, tile.rendimiento_m2, merma=self._merma
                )
            elif piezas is not None:
                cant = paquetes(piezas, tile.piezas_por_paquete)
            else:
                cant = math.ceil(s.area_m2 * (1 + self._merma))
            det = (
                f"{piezas} piezas ≈ {cant} {tile.unidad}(s) para {s.area_m2:g} m²"
                if piezas is not None
                else f"{cant} {tile.unidad}(s) para {s.area_m2:g} m²"
            )
            lineas.append(self._linea(tile, etiqueta, "principal", cant, s.area_m2, det, piezas))

            # Adhesivo (pegazulejo).
            if s.adhesivo_producto_id:
                adh = self._req(prods, s.adhesivo_producto_id, "adhesivo")
                sacos = unidades_por_rendimiento(
                    s.area_m2, adh.rendimiento_m2 or 0, merma=self._merma
                )
                lineas.append(
                    self._linea(
                        adh, etiqueta, "adhesivo", sacos, s.area_m2,
                        f"{sacos} {adh.unidad}(s) para {s.area_m2:g} m²", None,
                    )
                )

            # Crucetas (dependen de las piezas + método).
            if s.cruceta_producto_id:
                cruc = self._req(prods, s.cruceta_producto_id, "cruceta")
                if piezas is None:
                    raise ValidationError(
                        "La loseta principal no trae dimensiones de pieza; "
                        "no se pueden calcular las crucetas."
                    )
                if not cruc.piezas_por_paquete or cruc.piezas_por_paquete <= 0:
                    # Las crucetas NUNCA se venden sueltas; un piezas_por_paquete
                    # faltante o en 0 (dato de catálogo incompleto) haría que
                    # paquetes() cotizara cada pieza suelta al precio de la
                    # bolsa completa (ej. 900 piezas × $35 = $31,500 en vez de
                    # ~15 bolsas × $35). Se corta acá en vez de cobrar de más.
                    raise ValidationError(
                        f"El producto de crucetas '{cruc.nombre}' no tiene "
                        "piezas_por_paquete configurado en el catálogo del "
                        "proveedor; no se puede cotizar por pieza suelta. "
                        "Repórtalo al proveedor para que lo corrija."
                    )
                if s.metodo_crucetas not in CRUCETAS_POR_PIEZA:
                    raise ValidationError(
                        f"metodo_crucetas inválido: {s.metodo_crucetas!r}."
                    )
                total = crucetas_necesarias(piezas, metodo=s.metodo_crucetas)
                paqs = paquetes(total, cruc.piezas_por_paquete)
                lineas.append(
                    self._linea(
                        cruc, etiqueta, "cruceta", paqs, s.area_m2,
                        f"{total} crucetas ({s.metodo_crucetas}) ≈ "
                        f"{paqs} {cruc.unidad}(s)", None,
                    )
                )

            # Boquilla (junta / detallado).
            if s.boquilla_producto_id:
                boq = self._req(prods, s.boquilla_producto_id, "boquilla")
                unid = unidades_por_rendimiento(
                    s.area_m2, boq.rendimiento_m2 or 0, merma=self._merma
                )
                lineas.append(
                    self._linea(
                        boq, etiqueta, "boquilla", unid, s.area_m2,
                        f"{unid} {boq.unidad}(s) para {s.area_m2:g} m²", None,
                    )
                )

        if cmd.mano_obra:
            lineas.append(
                LineaCotizacion(
                    material_id=None,
                    proveedor_id=None,
                    proveedor_nombre="Mano de obra",
                    proveedor_distancia=None,
                    descripcion="Mano de obra",
                    cantidad=1,
                    unidad="servicio",
                    precio_unitario=cmd.mano_obra,
                    subtotal=round(cmd.mano_obra, 2),
                )
            )

        total = round(sum(ln.subtotal for ln in lineas), 2)
        return await self._repo.crear(
            proyecto_id=cmd.proyecto_id,
            usuario_id=cmd.usuario_id,
            total=total,
            lineas=lineas,
        )

    @staticmethod
    def _req(prods, producto_id, rol):
        p = prods.get(producto_id)
        if p is None:
            raise ValidationError(
                f"Producto {rol} '{producto_id}' no disponible en proveedores."
            )
        return p

    @staticmethod
    def _linea(prod, etiqueta, rol, cantidad, area, detalle, piezas):
        subtotal = round(cantidad * prod.precio_unitario, 2)
        return LineaCotizacion(
            material_id=prod.producto_id,
            proveedor_id=prod.proveedor_id,
            proveedor_nombre=prod.proveedor_nombre,
            proveedor_distancia=prod.distancia_km,
            descripcion=f"{prod.nombre} ({etiqueta} · {rol}) — {detalle}",
            cantidad=cantidad,
            unidad=prod.unidad,
            precio_unitario=prod.precio_unitario,
            subtotal=subtotal,
            piezas=piezas,
            area_m2=area,
        )
