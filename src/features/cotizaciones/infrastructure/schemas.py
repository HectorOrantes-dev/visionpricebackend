"""Schemas HTTP de la feature cotizaciones."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


# --- Cálculo de m² ---
class CalculoRequest(BaseModel):
    grabacion_id: int | None = None
    texto: str | None = None
    # Overrides manuales: se combinan con lo que el regex detectó del texto/
    # transcripción (ej. la altura no se detectó y el usuario la escribe a
    # mano). Solo se reemplaza la dimensión que venga en el override.
    largo_m: float | None = Field(default=None, gt=0)
    ancho_m: float | None = Field(default=None, gt=0)
    alto_m: float | None = Field(default=None, gt=0)
    # Override de área final: para medir una sola superficie (ej. "una pared
    # de 2x2 m") sin pasar por la fórmula de perímetro de cuarto completo.
    piso_m2: float | None = Field(default=None, gt=0)
    paredes_m2: float | None = Field(default=None, gt=0)


class CalculoOut(BaseModel):
    largo_m: float | None
    ancho_m: float | None
    alto_m: float | None
    piso_m2: float | None
    paredes_m2: float | None
    advertencias: list[str]


# --- Productos cercanos ---
class ProductoCercanoOut(BaseModel):
    producto_id: str
    nombre: str
    categoria: str
    unidad: str
    precio_unitario: float
    rendimiento_m2: float | None
    image_url: str | None = None
    proveedor_id: str | None
    proveedor_nombre: str | None
    proveedor_lat: float | None = None
    proveedor_lng: float | None = None
    distancia_km: float | None
    pieza_largo_m: float | None = None
    pieza_ancho_m: float | None = None
    piezas_por_paquete: int | None = None


# --- Crear cotización ---
class ItemRequest(BaseModel):
    producto_id: str
    # Indica el área con UNA de las dos (area_m2 tiene prioridad):
    area_m2: float | None = Field(default=None, gt=0)
    aplicar_a: Literal["piso", "pared"] | None = None
    descripcion: str | None = Field(default=None, max_length=150)

    @model_validator(mode="after")
    def _tiene_area(self) -> "ItemRequest":
        if self.area_m2 is None and self.aplicar_a is None:
            raise ValueError("Cada ítem necesita area_m2 o aplicar_a.")
        return self


class CrearCotizacionRequest(BaseModel):
    proyecto_id: int
    piso_m2: float | None = Field(default=None, ge=0)
    paredes_m2: float | None = Field(default=None, ge=0)
    items: list[ItemRequest] = Field(min_length=1)
    # Monto fijo que el usuario cobra por instalación/servicio. Se agrega como
    # una línea más de la cotización (no depende de proveedores) y se suma al total.
    mano_obra: float | None = Field(default=None, gt=0)


class MaterialReglaOut(BaseModel):
    categoria: str
    metodo_calculo: str          # rendimiento | kit
    requiere_kit: bool
    complementos: list[str]


class SuperficieKitRequest(BaseModel):
    area_m2: float = Field(gt=0)
    principal_producto_id: str  # la loseta (piso/azulejo/zoclo)
    descripcion: str | None = Field(default=None, max_length=150)
    metodo_crucetas: Literal["interseccion", "tradicional", "nivelacion"] = (
        "tradicional"
    )
    adhesivo_producto_id: str | None = None
    cruceta_producto_id: str | None = None
    boquilla_producto_id: str | None = None


class CrearKitRequest(BaseModel):
    proyecto_id: int
    superficies: list[SuperficieKitRequest] = Field(min_length=1)
    mano_obra: float | None = Field(default=None, gt=0)
    # Si esta cotización se creó a partir de una sugerencia de
    # POST /recomendaciones/kit, mandar su recomendacion_id acá marca esa
    # recomendación como "usada" (contador de recomendaciones/metricas).
    recomendacion_id: int | None = None


class LineaOut(BaseModel):
    material_id: str | None
    proveedor_id: str | None
    descripcion: str
    cantidad: float
    unidad: str
    precio_unitario: float
    subtotal: float
    piezas: int | None = None
    area_m2: float | None = None


class CotizacionPdfOut(BaseModel):
    id: int
    # Número propio del usuario (1, 2, 3...) — esto es lo que se muestra en
    # UI/PDF como "Cotización #N". "id" es el PK global de la tabla
    # presupuestos (compartida por todos los usuarios): NO mostrarlo al
    # usuario, solo sirve para armar la URL de descarga del PDF.
    numero: int
    proyecto_id: int
    proyecto_nombre: str
    estado: str
    total: float
    fecha: datetime
    url_pdf: str


class UsoCotizacionesOut(BaseModel):
    plan_activo: str | None
    ilimitado: bool
    limite_gratis: int
    usadas: int
    restantes: int | None


class CotizacionOut(BaseModel):
    id: int
    numero: int
    proyecto_id: int
    estado: str
    total: float
    fecha: datetime
    mano_obra: float | None = None
    lineas: list[LineaOut]


# --- Borrador automático (voz -> extracción -> proveedores cercanos) ---
class SuperficieManualRequest(BaseModel):
    """Superficie puesta a mano cuando el audio no se entendió bien (o el
    ML no devolvió estructura): reemplaza por completo lo que haya llegado
    de la extracción para esta cotización."""
    categoria: Literal["piso", "azulejo", "zoclo", "pintura", "impermeabilizante"]
    descripcion: str | None = Field(default=None, max_length=150)
    # Una de las dos formas de dar el área (area_m2 tiene prioridad):
    area_m2: float | None = Field(default=None, gt=0)
    largo_m: float | None = Field(default=None, gt=0)
    ancho_m: float | None = Field(default=None, gt=0)
    alto_m: float | None = Field(default=None, gt=0)
    acabado: str | None = None
    manos_pintura: int | None = Field(default=None, gt=0)
    requiere_resane: bool = False

    @model_validator(mode="after")
    def _tiene_medida(self) -> "SuperficieManualRequest":
        if self.area_m2 is None and not (self.largo_m and self.ancho_m):
            raise ValueError(
                "Cada superficie manual necesita area_m2, o largo_m + ancho_m."
            )
        return self


class BorradorRequest(BaseModel):
    grabacion_id: int
    # Si vienen, se usan EN VEZ de lo que haya extraído el ML (para cuando el
    # audio no se entendió bien y el usuario mete las medidas a mano).
    superficies: list[SuperficieManualRequest] | None = None


class LineaBorradorOut(BaseModel):
    rol: str
    producto_id: str | None
    nombre: str
    proveedor_nombre: str | None
    distancia_km: float | None
    cantidad: float
    unidad: str
    precio_unitario: float
    subtotal: float
    detalle: str


class SuperficieBorradorOut(BaseModel):
    categoria: str
    descripcion: str | None
    area_m2: float | None
    metodo: str
    lineas: list[LineaBorradorOut]


class BorradorOut(BaseModel):
    proyecto_id: int
    grabacion_id: int
    superficies: list[SuperficieBorradorOut]
    total_estimado: float
    advertencias: list[str]
    cuerpo_confirmacion: dict
