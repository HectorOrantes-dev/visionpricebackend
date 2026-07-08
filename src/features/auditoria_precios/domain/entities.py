"""Entidades de dominio de auditoría de precios."""
from dataclasses import dataclass

from src.features.auditoria_precios.domain.estadistica import AnalisisPrecio


@dataclass
class LineaPrecio:
    detalle_id: int
    presupuesto_id: int
    material_id: str | None
    descripcion: str
    precio_unitario: float


@dataclass
class LineaAuditada:
    detalle_id: int
    presupuesto_id: int
    material_id: str | None
    descripcion: str
    precio_unitario: float
    analisis: AnalisisPrecio
