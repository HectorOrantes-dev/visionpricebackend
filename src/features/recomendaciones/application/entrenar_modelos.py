"""Caso de uso: (re)entrenar los dos modelos a partir del dataset de obras."""
from dataclasses import dataclass

from src.features.recomendaciones.domain.ports import ObrasDataset
from src.features.recomendaciones.infrastructure.modelos import ArbolTipoKit, KnnZona


@dataclass
class MetricasEntrenamiento:
    n_obras: int
    n_obras_reales: int
    n_obras_sinteticas: int
    accuracy_arbol_tipo_kit: float


class EntrenarModelos:
    def __init__(
        self,
        dataset: ObrasDataset,
        arbol: ArbolTipoKit,
        knn: KnnZona,
    ) -> None:
        self._dataset = dataset
        self._arbol = arbol
        self._knn = knn

    async def execute(self) -> MetricasEntrenamiento:
        obras = await self._dataset.cargar()
        n_reales = sum(1 for o in obras if o.origen == "real")

        accuracy = self._arbol.entrenar(obras)
        self._arbol.guardar()

        self._knn.entrenar(obras)
        self._knn.guardar()

        return MetricasEntrenamiento(
            n_obras=len(obras),
            n_obras_reales=n_reales,
            n_obras_sinteticas=len(obras) - n_reales,
            accuracy_arbol_tipo_kit=accuracy,
        )
