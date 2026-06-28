"""Casos de uso de auditoría de precios (estadística, sin ML)."""
from collections import defaultdict
from dataclasses import dataclass

from src.features.auditoria_precios.domain.entities import LineaAuditada
from src.features.auditoria_precios.domain.estadistica import (
    AnalisisPrecio,
    analizar,
)
from src.features.auditoria_precios.domain.ports import AuditoriaRepository
from src.shared.errors import NotFound


@dataclass
class ResultadoAuditoria:
    lineas: list[LineaAuditada]

    @property
    def total(self) -> int:
        return len(self.lineas)

    @property
    def anomalias(self) -> int:
        return sum(1 for ln in self.lineas if ln.analisis.es_anomalia)


def _sin_material() -> AnalisisPrecio:
    return AnalisisPrecio(
        precio=0,
        n_historico=0,
        mediana=None,
        es_anomalia=False,
        severidad="sin_datos",
        razones=["Línea sin material asociado; no se puede auditar."],
    )


class AuditarPresupuesto:
    """Audita cada línea de un presupuesto contra el histórico de su zona."""

    def __init__(
        self,
        repo: AuditoriaRepository,
        *,
        precision: int,
        margen: float,
        min_muestras: int,
    ) -> None:
        self._repo = repo
        self._precision = precision
        self._margen = margen
        self._min_muestras = min_muestras

    async def execute(self, presupuesto_id: int) -> ResultadoAuditoria:
        coords = await self._repo.coords_de_presupuesto(presupuesto_id)
        if coords is None:
            raise NotFound("Presupuesto no encontrado.")
        lat, lng = coords

        lineas = await self._repo.lineas_de_presupuesto(presupuesto_id)
        auditadas: list[LineaAuditada] = []
        for ln in lineas:
            if ln.material_id is None:
                analisis = _sin_material()
                analisis.precio = ln.precio_unitario
            else:
                hist = await self._repo.historico_precios(
                    ln.material_id,
                    lat=lat,
                    lng=lng,
                    precision=self._precision,
                    excluir_presupuesto=presupuesto_id,
                )
                analisis = analizar(
                    ln.precio_unitario,
                    hist,
                    min_muestras=self._min_muestras,
                    margen=self._margen,
                )
            auditadas.append(
                LineaAuditada(
                    detalle_id=ln.detalle_id,
                    presupuesto_id=ln.presupuesto_id,
                    material_id=ln.material_id,
                    descripcion=ln.descripcion,
                    precio_unitario=ln.precio_unitario,
                    analisis=analisis,
                )
            )
        return ResultadoAuditoria(lineas=auditadas)


@dataclass
class AuditarZonaQuery:
    lat: float
    lng: float


class AuditarZona:
    """Escanea una zona: marca las líneas anómalas por material."""

    def __init__(
        self,
        repo: AuditoriaRepository,
        *,
        precision: int,
        margen: float,
        min_muestras: int,
    ) -> None:
        self._repo = repo
        self._precision = precision
        self._margen = margen
        self._min_muestras = min_muestras

    async def execute(self, query: AuditarZonaQuery) -> ResultadoAuditoria:
        lineas = await self._repo.lineas_en_zona(
            lat=query.lat, lng=query.lng, precision=self._precision
        )
        # Distribución de precios por material dentro de la zona.
        por_material: dict[int, list[float]] = defaultdict(list)
        for ln in lineas:
            if ln.material_id is not None:
                por_material[ln.material_id].append(ln.precio_unitario)

        anomalas: list[LineaAuditada] = []
        for ln in lineas:
            if ln.material_id is None:
                continue
            analisis = analizar(
                ln.precio_unitario,
                por_material[ln.material_id],
                min_muestras=self._min_muestras,
                margen=self._margen,
            )
            if analisis.es_anomalia:
                anomalas.append(
                    LineaAuditada(
                        detalle_id=ln.detalle_id,
                        presupuesto_id=ln.presupuesto_id,
                        material_id=ln.material_id,
                        descripcion=ln.descripcion,
                        precio_unitario=ln.precio_unitario,
                        analisis=analisis,
                    )
                )
        return ResultadoAuditoria(lineas=anomalas)
