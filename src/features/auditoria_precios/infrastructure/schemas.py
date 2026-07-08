"""Schemas HTTP de auditoría de precios."""
from pydantic import BaseModel


class AnalisisOut(BaseModel):
    n_historico: int
    mediana: float | None
    es_anomalia: bool
    severidad: str
    razones: list[str]
    limite_inferior: float | None
    limite_superior: float | None


class LineaAuditadaOut(BaseModel):
    detalle_id: int
    presupuesto_id: int
    material_id: str | None
    descripcion: str
    precio_unitario: float
    analisis: AnalisisOut


class AuditoriaOut(BaseModel):
    total: int
    anomalias: int
    lineas: list[LineaAuditadaOut]
