"""Adaptador REAL de ObrasDataset: lee presupuestos/detalle_presupuesto ya
creados en el sistema (no sintéticos) y los convierte a `Obra`.

Limitaciones actuales del esquema (documentadas, no ocultas):
  - `detalle_presupuesto` no persiste `area_m2` como columna: se parsea del
    texto de `descripcion_actividad` (formato fijo, ver motor_materiales.py /
    crear_kit.py: "... para {area:g} m²"). Si una línea no matchea ese
    patrón, se descarta (no se inventa un área).
  - `metodo_crucetas` NO se persiste en ningún lado hoy (crear_kit.py lo usa
    para calcular la cantidad de crucetas y lo descarta) — las obras reales
    salen siempre con `metodo_crucetas=None`. Para que esto deje de ser una
    limitación hay que agregar la columna y guardarla al crear el kit.
  - Requiere que el `Proyecto` tenga `latitud`/`longitud` cargados; los que
    no los tienen se excluyen (no hay zona que asignarles).
"""
import re
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.cotizaciones.domain.ports import ProveedoresPort
from src.features.cotizaciones.domain.reglas_material import regla_de
from src.features.recomendaciones.domain.entities import Obra
from src.features.recomendaciones.domain.ports import ObrasDataset
from src.shared.models import DetallePresupuesto, Presupuesto, Proyecto

_COMPLEMENTO_CATEGORIAS = {"pegazulejo", "cruceta", "emboquillador"}
_RE_AREA = re.compile(r"para\s+([\d]+(?:[.,]\d+)?)\s*m")


class ObrasDatasetReal(ObrasDataset):
    def __init__(self, session: AsyncSession, proveedores: ProveedoresPort) -> None:
        self._session = session
        self._proveedores = proveedores

    async def cargar(self) -> list[Obra]:
        result = await self._session.execute(
            select(
                Presupuesto.id.label("presupuesto_id"),
                Proyecto.nombre.label("proyecto_nombre"),
                Proyecto.latitud,
                Proyecto.longitud,
                DetallePresupuesto.material_id,
                DetallePresupuesto.descripcion_actividad,
            )
            .join(Proyecto, Proyecto.id == Presupuesto.proyecto_id)
            .join(
                DetallePresupuesto,
                DetallePresupuesto.presupuesto_id == Presupuesto.id,
            )
            .where(
                Presupuesto.estado.in_(["borrador", "confirmado"]),
                Proyecto.latitud.is_not(None),
                Proyecto.longitud.is_not(None),
                DetallePresupuesto.material_id.is_not(None),
            )
        )
        filas = result.all()
        if not filas:
            return []

        material_ids = {f.material_id for f in filas}
        productos = {
            p.producto_id: p
            for p in await self._proveedores.productos_por_ids(list(material_ids))
        }

        # Agrupar líneas por presupuesto para poder cruzar principal + complementos.
        por_presupuesto: dict[int, list] = defaultdict(list)
        for f in filas:
            por_presupuesto[f.presupuesto_id].append(f)

        obras: list[Obra] = []
        for presupuesto_id, lineas in por_presupuesto.items():
            complementos_del_presupuesto: list[str] = []
            principales = []
            for f in lineas:
                prod = productos.get(f.material_id)
                if prod is None:
                    continue
                categoria = (prod.categoria or "").lower().strip()
                if categoria in _COMPLEMENTO_CATEGORIAS:
                    complementos_del_presupuesto.append(categoria)
                else:
                    principales.append((f, categoria))

            for f, categoria in principales:
                m = _RE_AREA.search(f.descripcion_actividad or "")
                if not m:
                    continue  # sin área parseable, no se puede usar esta línea
                area_m2 = float(m.group(1).replace(",", "."))

                regla = regla_de(categoria)
                obras.append(
                    Obra(
                        obra_id=presupuesto_id,
                        lat=float(f.latitud),
                        lng=float(f.longitud),
                        zona_nombre=f.proyecto_nombre,
                        categoria=categoria,
                        area_m2=area_m2,
                        tipo_kit="kit" if regla.requiere_kit else "rendimiento",
                        # No persistido hoy (ver docstring del módulo).
                        metodo_crucetas=None,
                        complementos_usados=list(set(complementos_del_presupuesto)),
                        origen="real",
                    )
                )
        return obras
