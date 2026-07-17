"""Caso de uso: recomendar tipo de kit + complementos para una obra nueva.

Tres pasos:
  1) Árbol Gini → ¿es kit o rendimiento simple?
  2) Si es kit → K-NN geográfico entre obras de la MISMA categoría → qué
     complementos y método de junta se usaron más en la zona.
  3) Cruzar cada categoría (principal + complementos) con productos REALES y
     cercanos de Proveedores — sin esto, la recomendación queda en el nivel
     "categoría" y no en "qué comprar".
"""
from collections import Counter

from src.core.config import settings
from src.features.cotizaciones.domain.ports import ProveedoresPort
from src.features.recomendaciones.domain.entities import ObraNueva, RecomendacionKit
from src.features.recomendaciones.domain.ports import (
    ClasificadorTipoKit,
    RecomendacionUsoRepository,
    RecomendadorZona,
    RecomendarKitPort,
)
from src.shared.errors import ValidationError

# Un complemento se recomienda solo si aparece en al menos esta fracción de
# los vecinos — evita recomendar algo que un solo vecino atípico usó.
_UMBRAL_COMPLEMENTO = 0.5
# Cuántos productos concretos mostrar por categoría (los más cercanos primero,
# ya vienen ordenados así desde Proveedores).
_MAX_PRODUCTOS_POR_CATEGORIA = 3


class RecomendarKit(RecomendarKitPort):
    def __init__(
        self,
        arbol: ClasificadorTipoKit,
        knn: RecomendadorZona,
        auditoria: RecomendacionUsoRepository,
        proveedores: ProveedoresPort,
    ) -> None:
        self._arbol = arbol
        self._knn = knn
        self._auditoria = auditoria
        self._proveedores = proveedores

    async def recomendar(
        self, obra: ObraNueva, k: int = 15, *, usuario_id: int
    ) -> RecomendacionKit:
        if obra.area_m2 <= 0:
            raise ValidationError("area_m2 debe ser mayor a 0.")

        resultado = self._construir_recomendacion(obra, k)
        resultado.materiales_recomendados = await self._buscar_materiales(
            obra, resultado.complementos_recomendados
        )

        recomendacion_id = await self._auditoria.registrar_solicitud(
            usuario_id=usuario_id,
            proyecto_id=obra.proyecto_id,
            recomendacion=resultado,
            categoria=obra.categoria,
        )
        resultado.recomendacion_id = recomendacion_id
        return resultado

    async def _buscar_materiales(
        self, obra: ObraNueva, complementos: list[str]
    ) -> dict[str, list]:
        categorias = [obra.categoria, *complementos]
        materiales: dict[str, list] = {}
        for categoria in categorias:
            productos = await self._proveedores.productos_cercanos(
                lat=obra.lat,
                lng=obra.lng,
                radio_km=settings.providers_radio_km_default,
                categoria=categoria,
            )
            if productos:
                materiales[categoria] = productos[:_MAX_PRODUCTOS_POR_CATEGORIA]
        return materiales

    def _construir_recomendacion(self, obra: ObraNueva, k: int) -> RecomendacionKit:
        tipo_kit, confianza = self._arbol.predecir(obra.categoria, obra.area_m2)

        if tipo_kit != "kit":
            return RecomendacionKit(
                tipo_kit=tipo_kit,
                confianza_tipo_kit=confianza,
                complementos_recomendados=[],
                metodo_crucetas_recomendado=None,
                zona_referencia=None,
                n_obras_similares=0,
            )

        vecinos = self._knn.vecinos_mas_cercanos(
            lat=obra.lat, lng=obra.lng, categoria=obra.categoria, k=k
        )
        if not vecinos:
            return RecomendacionKit(
                tipo_kit=tipo_kit,
                confianza_tipo_kit=confianza,
                complementos_recomendados=["pegazulejo", "cruceta", "emboquillado"],
                metodo_crucetas_recomendado="tradicional",
                zona_referencia=None,
                n_obras_similares=0,
            )

        n = len(vecinos)
        conteo_complementos: Counter[str] = Counter()
        for v in vecinos:
            conteo_complementos.update(v.complementos_usados)
        complementos = [
            nombre
            for nombre, cuenta in conteo_complementos.items()
            if cuenta / n >= _UMBRAL_COMPLEMENTO
        ]

        metodos = [v.metodo_crucetas for v in vecinos if v.metodo_crucetas]
        metodo_mas_comun = (
            Counter(metodos).most_common(1)[0][0] if metodos else None
        )

        zona_mas_comun = Counter(v.zona_nombre for v in vecinos).most_common(1)[0][0]

        return RecomendacionKit(
            tipo_kit=tipo_kit,
            confianza_tipo_kit=confianza,
            complementos_recomendados=complementos,
            metodo_crucetas_recomendado=metodo_mas_comun,
            zona_referencia=zona_mas_comun,
            n_obras_similares=n,
        )
