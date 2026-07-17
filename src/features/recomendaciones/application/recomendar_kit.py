"""Caso de uso: recomendar tipo de kit + complementos para una obra nueva.

Dos pasos:
  1) Árbol Gini → ¿es kit o rendimiento simple?
  2) Si es kit → K-NN geográfico entre obras de la MISMA categoría → qué
     complementos y método de junta se usaron más en la zona.
"""
from collections import Counter

from src.features.recomendaciones.domain.entities import ObraNueva, RecomendacionKit
from src.features.recomendaciones.domain.ports import (
    ClasificadorTipoKit,
    RecomendadorZona,
    RecomendarKitPort,
)
from src.shared.errors import ValidationError

# Un complemento se recomienda solo si aparece en al menos esta fracción de
# los vecinos — evita recomendar algo que un solo vecino atípico usó.
_UMBRAL_COMPLEMENTO = 0.5


class RecomendarKit(RecomendarKitPort):
    def __init__(
        self,
        arbol: ClasificadorTipoKit,
        knn: RecomendadorZona,
    ) -> None:
        self._arbol = arbol
        self._knn = knn

    async def recomendar(self, obra: ObraNueva, k: int = 15) -> RecomendacionKit:
        if obra.area_m2 <= 0:
            raise ValidationError("area_m2 debe ser mayor a 0.")

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
                complementos_recomendados=["pegazulejo", "cruceta", "boquilla"],
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
