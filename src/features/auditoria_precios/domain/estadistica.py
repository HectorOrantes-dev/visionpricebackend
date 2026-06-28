"""Detección de anomalías de precio por estadística robusta (sin ML).

Combina tres señales, todas explicables:
  1. Margen fijo vs mediana de la zona (sobreprecio / subprecio).
  2. IQR: fuera de [Q1 - 1.5·IQR, Q3 + 1.5·IQR] (crítico si fuera de 3·IQR).
  3. MAD (desviación absoluta mediana): z robusto |z| > 3.5.

Devuelve un veredicto con razones en lenguaje natural, listo para auditoría.
"""
import statistics
from dataclasses import dataclass, field


@dataclass
class AnalisisPrecio:
    precio: float
    n_historico: int
    mediana: float | None
    es_anomalia: bool
    severidad: str  # sin_datos | normal | revisar | critico
    razones: list[str] = field(default_factory=list)
    limite_inferior: float | None = None
    limite_superior: float | None = None


def _mad(data: list[float], mediana: float) -> float:
    return statistics.median([abs(x - mediana) for x in data])


def analizar(
    precio: float,
    historico: list[float],
    *,
    min_muestras: int = 5,
    margen: float = 0.30,
) -> AnalisisPrecio:
    n = len(historico)
    if n < 3:
        return AnalisisPrecio(
            precio=precio,
            n_historico=n,
            mediana=None,
            es_anomalia=False,
            severidad="sin_datos",
            razones=["Histórico insuficiente para auditar (se necesitan ≥3 referencias)."],
        )

    mediana = statistics.median(historico)
    razones: list[str] = []
    anomalia = False
    severidad = "normal"
    li = ls = None

    # 1) Margen fijo vs mediana.
    if mediana > 0:
        ratio = precio / mediana
        if ratio >= 1 + margen:
            razones.append(
                f"Sobreprecio: {(ratio - 1) * 100:.0f}% por encima de la mediana "
                f"de la zona (${mediana:,.2f})."
            )
            anomalia = True
        elif ratio <= 1 - margen:
            razones.append(
                f"Precio bajo: {(1 - ratio) * 100:.0f}% por debajo de la mediana "
                f"(${mediana:,.2f}); posible error de unidad."
            )
            anomalia = True

    if n >= min_muestras:
        # 2) IQR.
        q1, _, q3 = statistics.quantiles(historico, n=4, method="inclusive")
        iqr = q3 - q1
        if iqr > 0:
            li = q1 - 1.5 * iqr
            ls = q3 + 1.5 * iqr
            if precio < li or precio > ls:
                anomalia = True
                razones.append(
                    f"Fuera del rango habitual de la zona "
                    f"[${li:,.2f} – ${ls:,.2f}] (IQR)."
                )
                if precio < q1 - 3 * iqr or precio > q3 + 3 * iqr:
                    severidad = "critico"

        # 3) MAD (robusto).
        mad = _mad(historico, mediana)
        if mad > 0:
            mz = 0.6745 * (precio - mediana) / mad
            if abs(mz) > 3.5:
                anomalia = True
                razones.append(f"Desviación robusta alta (MAD z={mz:.1f}).")
                if abs(mz) > 5:
                    severidad = "critico"

    if anomalia and severidad == "normal":
        severidad = "revisar"
    if not anomalia:
        razones.append("Dentro del rango normal de la zona.")

    return AnalisisPrecio(
        precio=precio,
        n_historico=n,
        mediana=round(mediana, 2),
        es_anomalia=anomalia,
        severidad=severidad,
        razones=razones,
        limite_inferior=round(li, 2) if li is not None else None,
        limite_superior=round(ls, 2) if ls is not None else None,
    )
