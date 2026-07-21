"""Caso de uso: validar/normalizar el parametros_json crudo del microservicio
de ML contra el schema rígido de piso/pintura (ParametrosExtraidos).

Es tolerante (igual que cotizaciones.domain.calculo): lo que no se pueda
determinar queda en None con una advertencia, para que la app pida el dato a
mano en vez de fallar la extracción completa.
"""
from src.features.cotizaciones.domain.calculo import calcular_areas
from src.features.cotizaciones.domain.entities import Dimensiones
from src.features.cotizaciones.domain.reglas_material import regla_de
from src.features.extracciones.domain.entities import (
    ParametrosExtraidos,
    SuperficieExtraida,
)

_CATEGORIAS_VALIDAS = {"piso", "azulejo", "zoclo", "pintura", "impermeabilizante"}


class ValidarExtraccion:
    def execute(
        self, parametros_json: dict | None, texto_fallback: str | None = None
    ) -> ParametrosExtraidos:
        advertencias: list[str] = []

        raw_superficies: list[dict] = []
        if isinstance(parametros_json, dict):
            raw_superficies = parametros_json.get("superficies") or []
            # Payload plano de una sola superficie (sin envolver en lista).
            if not raw_superficies and parametros_json.get("categoria"):
                raw_superficies = [parametros_json]

        superficies: list[SuperficieExtraida] = []
        for raw in raw_superficies:
            categoria = str(raw.get("categoria") or raw.get("tipo") or "").lower().strip()
            if categoria not in _CATEGORIAS_VALIDAS:
                advertencias.append(
                    f"Categoría desconocida '{categoria or '(vacía)'}'; "
                    f"se cotizará por rendimiento genérico. Usa {', '.join(sorted(_CATEGORIAS_VALIDAS))}."
                )
                # regla_de() ya tiene fallback a "rendimiento" para categorías
                # desconocidas, así que se deja pasar tal cual.

            area = raw.get("area_m2")
            largo, ancho, alto = raw.get("largo_m"), raw.get("ancho_m"), raw.get("alto_m")
            if area is None and largo and ancho:
                calc = calcular_areas(Dimensiones(largo_m=largo, ancho_m=ancho, alto_m=alto))
                # Pintura de muros usa el área de paredes (perímetro × alto);
                # el resto (piso/azulejo/zoclo) usa el área de piso. Se filtra
                # la advertencia de la dimensión que esta superficie no usa.
                regla = regla_de(categoria)
                es_pintura = regla.categoria == "pintura"
                area = calc.paredes_m2 if es_pintura else calc.piso_m2
                irrelevante = "el piso" if es_pintura else "las paredes"
                advertencias.extend(a for a in calc.advertencias if irrelevante not in a)

            if area is None:
                advertencias.append(
                    f"No se pudo determinar el área para '{categoria or 'superficie'}'."
                )

            superficies.append(
                SuperficieExtraida(
                    categoria=categoria,
                    area_m2=area,
                    largo_m=largo,
                    ancho_m=ancho,
                    alto_m=alto,
                    descripcion=raw.get("descripcion"),
                    acabado=raw.get("acabado"),
                    manos_pintura=raw.get("manos_pintura"),
                    requiere_resane=bool(raw.get("requiere_resane", False)),
                )
            )

        if not superficies:
            advertencias.append(
                "El microservicio de ML no devolvió superficies estructuradas; "
                "usa POST /cotizaciones/calculo con el texto de la transcripción."
                if texto_fallback
                else "No hay datos de extracción todavía para esta grabación."
            )

        return ParametrosExtraidos(
            superficies=superficies,
            notas=parametros_json.get("notas") if isinstance(parametros_json, dict) else None,
            advertencias=advertencias,
        )
