"""Combina el dataset real (presupuestos ya creados) con el sintético.

El sintético actúa como relleno para que los modelos tengan suficientes
tuplas incluso con poco historial real todavía; a medida que haya más
cotizaciones reales, su peso relativo en el entrenamiento crece solo.
"""
from src.features.recomendaciones.domain.entities import Obra
from src.features.recomendaciones.domain.ports import ObrasDataset


class ObrasDatasetCombinado(ObrasDataset):
    def __init__(self, real: ObrasDataset, sintetico: ObrasDataset) -> None:
        self._real = real
        self._sintetico = sintetico

    async def cargar(self) -> list[Obra]:
        reales = await self._real.cargar()
        sinteticas = await self._sintetico.cargar()
        return reales + sinteticas
