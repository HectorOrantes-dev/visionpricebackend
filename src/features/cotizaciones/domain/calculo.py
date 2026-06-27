"""Cálculo de m² de piso y paredes a partir de la transcripción (reglas/regex).

El motor de IA solo transcribe; aquí extraemos largo/ancho/alto del texto y
calculamos:
  - piso    = largo × ancho
  - paredes = 2 × (largo + ancho) × alto   (perímetro × altura)

Es tolerante: si no detecta algo, lo deja en None y agrega una advertencia para
que la app pida la medida a mano (fallback manual).
"""
import re

from src.features.cotizaciones.domain.entities import CalculoAreas, Dimensiones

_NUM = r"(\d+(?:[.,]\d+)?)"

# Palabras-número básicas (es) para frases como "cuatro por cinco".
_PALABRAS = {
    "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
    "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15,
}


def _to_float(s: str | None) -> float | None:
    if not s:
        return None
    return float(s.replace(",", "."))


def _sustituir_palabras(texto: str) -> str:
    def repl(m: re.Match) -> str:
        return str(_PALABRAS[m.group(0)])

    patron = r"\b(" + "|".join(_PALABRAS) + r")\b"
    return re.sub(patron, repl, texto)


def parse_dimensiones(texto: str) -> Dimensiones:
    t = _sustituir_palabras(texto.lower())
    largo = ancho = alto = None

    # "A x B", "A por B", "A * B"
    m = re.search(rf"{_NUM}\s*(?:x|por|\*)\s*{_NUM}", t)
    if m:
        largo = _to_float(m.group(1))
        ancho = _to_float(m.group(2))

    # alto: "alto/altura (de) N"  ó  "N (m/metros) de alto/altura"
    m = re.search(rf"(?:alto|altura)\s*(?:de\s*)?{_NUM}", t)
    if m is None:
        m = re.search(rf"{_NUM}\s*(?:m|metros?)?\s*de\s*(?:alto|altura)", t)
    if m:
        alto = _to_float(m.group(1))

    return Dimensiones(largo_m=largo, ancho_m=ancho, alto_m=alto)


def calcular_areas(dim: Dimensiones) -> CalculoAreas:
    advertencias: list[str] = []
    piso = paredes = None

    if dim.largo_m and dim.ancho_m:
        piso = round(dim.largo_m * dim.ancho_m, 2)
    else:
        advertencias.append(
            "No se detectaron largo y ancho; ingrésalos para calcular el piso."
        )

    if dim.largo_m and dim.ancho_m and dim.alto_m:
        paredes = round(2 * (dim.largo_m + dim.ancho_m) * dim.alto_m, 2)
    elif dim.alto_m is None:
        advertencias.append(
            "No se detectó la altura; ingrésala para calcular las paredes."
        )

    return CalculoAreas(
        largo_m=dim.largo_m,
        ancho_m=dim.ancho_m,
        alto_m=dim.alto_m,
        piso_m2=piso,
        paredes_m2=paredes,
        advertencias=advertencias,
    )


def calcular_desde_texto(texto: str) -> CalculoAreas:
    return calcular_areas(parse_dimensiones(texto))
