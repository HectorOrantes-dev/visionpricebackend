"""Caso de uso: generar el borrador automático de cotización de una grabación.

Cierra el flujo voz → presupuesto: toma la extracción validada (piso/pintura),
busca proveedores cercanos a la ubicación del proyecto y AUTO-SELECCIONA el
producto más barato de cada superficie (y sus complementos, si es un kit),
pero NO persiste nada — el usuario confirma o ajusta la selección con el
`cuerpo_confirmacion` devuelto, que se manda tal cual a POST /cotizaciones o
POST /cotizaciones/kit (los casos de uso que sí crean y cobran).
"""
import math
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from src.features.cotizaciones.domain.entities import (
    BorradorCotizacion,
    LineaBorrador,
    ProductoCercano,
    SuperficieBorrador,
)
from src.features.cotizaciones.domain.motor_instalacion import (
    crucetas_necesarias,
    paquetes,
    piezas_necesarias,
    unidades_por_rendimiento,
)
from src.features.cotizaciones.domain.motor_materiales import calcular_material
from src.features.cotizaciones.domain.ports import CotizacionRepository, ProveedoresPort
from src.features.cotizaciones.domain.reglas_material import regla_de
from src.features.extracciones.application.validar_extraccion import ValidarExtraccion
from src.shared.errors import Forbidden, NotFound, ValidationError
from src.shared.proyecto_acceso import puede_acceder as _puede_acceder

_ROL_COMPLEMENTO = {
    "pegazulejo": "adhesivo",
    "cruceta": "cruceta",
    "emboquillado": "boquilla",
}


@dataclass
class GenerarBorradorCommand:
    grabacion_id: int
    usuario_id: int


class GenerarBorradorCotizacion:
    def __init__(
        self,
        repo: CotizacionRepository,
        proveedores: ProveedoresPort,
        validar: ValidarExtraccion,
        session: AsyncSession,
        radio_km_default: float,
        merma: float = 0.08,
    ) -> None:
        self._repo = repo
        self._proveedores = proveedores
        self._validar = validar
        self._session = session
        self._radio_km = radio_km_default
        self._merma = merma

    async def execute(self, cmd: GenerarBorradorCommand) -> BorradorCotizacion:
        datos = await self._repo.datos_para_borrador(cmd.grabacion_id)
        if datos is None:
            raise NotFound("Grabación no encontrada o sin proyecto asociado.")

        if not await _puede_acceder(self._session, datos.proyecto_id, cmd.usuario_id):
            raise Forbidden("No tienes acceso a este proyecto.")

        if datos.lat is None or datos.lng is None:
            raise ValidationError(
                "El proyecto no tiene ubicación (lat/lng); no se pueden buscar "
                "proveedores cercanos."
            )

        parametros = self._validar.execute(datos.parametros_json, datos.texto)
        advertencias = list(parametros.advertencias)

        superficies_out: list[SuperficieBorrador] = []
        kit_body: list[dict] = []
        simple_body: list[dict] = []
        total = 0.0

        for sup in parametros.superficies:
            if sup.area_m2 is None:
                advertencias.append(
                    f"Se omitió '{sup.categoria or 'superficie'}': sin área calculada."
                )
                continue

            regla = regla_de(sup.categoria)
            candidatos = await self._proveedores.productos_cercanos(
                lat=datos.lat, lng=datos.lng, radio_km=self._radio_km,
                categoria=sup.categoria,
            )
            if not candidatos:
                advertencias.append(
                    f"No se encontraron proveedores cercanos para '{sup.categoria}'."
                )
                continue

            principal = min(candidatos, key=lambda p: p.precio_unitario)
            etiqueta = sup.descripcion or sup.categoria

            if regla.requiere_kit:
                lineas, seleccion, subtotal_kit, avisos = await self._armar_kit(
                    datos.lat, datos.lng, sup.area_m2, principal, etiqueta, regla.complementos
                )
                advertencias.extend(avisos)
                total += subtotal_kit
                kit_body.append(seleccion)
                metodo = "kit"
            else:
                calc = calcular_material(sup.area_m2, principal, merma=self._merma)
                subtotal = round(calc.cantidad * principal.precio_unitario, 2)
                total += subtotal
                lineas = [
                    LineaBorrador(
                        rol="material",
                        producto_id=principal.producto_id,
                        nombre=principal.nombre,
                        proveedor_nombre=principal.proveedor_nombre,
                        distancia_km=principal.distancia_km,
                        cantidad=calc.cantidad,
                        unidad=calc.unidad,
                        precio_unitario=principal.precio_unitario,
                        subtotal=subtotal,
                        detalle=calc.detalle,
                    )
                ]
                simple_body.append(
                    {
                        "producto_id": principal.producto_id,
                        "area_m2": sup.area_m2,
                        "descripcion": etiqueta,
                    }
                )
                metodo = "rendimiento"

            superficies_out.append(
                SuperficieBorrador(
                    categoria=sup.categoria,
                    descripcion=sup.descripcion,
                    area_m2=sup.area_m2,
                    metodo=metodo,
                    lineas=lineas,
                )
            )

        cuerpo_confirmacion: dict = {}
        if simple_body:
            cuerpo_confirmacion["simple"] = {
                "proyecto_id": datos.proyecto_id,
                "items": simple_body,
            }
        if kit_body:
            cuerpo_confirmacion["kit"] = {
                "proyecto_id": datos.proyecto_id,
                "superficies": kit_body,
            }

        return BorradorCotizacion(
            proyecto_id=datos.proyecto_id,
            grabacion_id=cmd.grabacion_id,
            superficies=superficies_out,
            total_estimado=round(total, 2),
            advertencias=advertencias,
            cuerpo_confirmacion=cuerpo_confirmacion,
        )

    async def _armar_kit(
        self,
        lat: float,
        lng: float,
        area_m2: float,
        principal: ProductoCercano,
        etiqueta: str,
        complementos: list[str],
    ) -> tuple[list[LineaBorrador], dict, float, list[str]]:
        avisos: list[str] = []
        lineas: list[LineaBorrador] = []
        subtotal_total = 0.0

        piezas = None
        if principal.pieza_largo_m and principal.pieza_ancho_m:
            piezas = piezas_necesarias(
                area_m2, principal.pieza_largo_m, principal.pieza_ancho_m,
                merma=self._merma,
            )

        if principal.rendimiento_m2:
            cant = unidades_por_rendimiento(area_m2, principal.rendimiento_m2, merma=self._merma)
        elif piezas is not None:
            cant = paquetes(piezas, principal.piezas_por_paquete)
        else:
            cant = math.ceil(area_m2 * (1 + self._merma))

        subtotal = round(cant * principal.precio_unitario, 2)
        subtotal_total += subtotal
        lineas.append(
            LineaBorrador(
                rol="principal",
                producto_id=principal.producto_id,
                nombre=principal.nombre,
                proveedor_nombre=principal.proveedor_nombre,
                distancia_km=principal.distancia_km,
                cantidad=cant,
                unidad=principal.unidad,
                precio_unitario=principal.precio_unitario,
                subtotal=subtotal,
                detalle=f"{cant} {principal.unidad}(s) para {area_m2:g} m²",
            )
        )

        seleccion = {
            "area_m2": area_m2,
            "principal_producto_id": principal.producto_id,
            "descripcion": etiqueta,
            "metodo_crucetas": "tradicional",
        }

        for complemento in complementos:
            rol = _ROL_COMPLEMENTO.get(complemento, complemento)
            comp_candidatos = await self._proveedores.productos_cercanos(
                lat=lat, lng=lng, radio_km=self._radio_km, categoria=complemento
            )
            if not comp_candidatos:
                avisos.append(
                    f"No se encontró '{complemento}' cercano para '{etiqueta}'; "
                    "agrégalo manualmente antes de confirmar."
                )
                continue
            comp = min(comp_candidatos, key=lambda p: p.precio_unitario)

            if rol == "cruceta":
                if piezas is None:
                    avisos.append(
                        f"No se pudieron calcular crucetas para '{etiqueta}' "
                        "(la loseta principal no trae dimensiones de pieza)."
                    )
                    continue
                total_crucetas = crucetas_necesarias(piezas, metodo="tradicional")
                cant_c = paquetes(total_crucetas, comp.piezas_por_paquete)
                subtotal_c = round(cant_c * comp.precio_unitario, 2)
                subtotal_total += subtotal_c
                lineas.append(
                    LineaBorrador(
                        rol="cruceta",
                        producto_id=comp.producto_id,
                        nombre=comp.nombre,
                        proveedor_nombre=comp.proveedor_nombre,
                        distancia_km=comp.distancia_km,
                        cantidad=cant_c,
                        unidad=comp.unidad,
                        precio_unitario=comp.precio_unitario,
                        subtotal=subtotal_c,
                        detalle=f"{total_crucetas} crucetas ≈ {cant_c} {comp.unidad}(s)",
                    )
                )
                seleccion["cruceta_producto_id"] = comp.producto_id
            else:
                cant_u = unidades_por_rendimiento(area_m2, comp.rendimiento_m2 or 0, merma=self._merma)
                subtotal_u = round(cant_u * comp.precio_unitario, 2)
                subtotal_total += subtotal_u
                lineas.append(
                    LineaBorrador(
                        rol=rol,
                        producto_id=comp.producto_id,
                        nombre=comp.nombre,
                        proveedor_nombre=comp.proveedor_nombre,
                        distancia_km=comp.distancia_km,
                        cantidad=cant_u,
                        unidad=comp.unidad,
                        precio_unitario=comp.precio_unitario,
                        subtotal=subtotal_u,
                        detalle=f"{cant_u} {comp.unidad}(s) para {area_m2:g} m²",
                    )
                )
                seleccion[f"{rol}_producto_id"] = comp.producto_id

        return lineas, seleccion, subtotal_total, avisos
