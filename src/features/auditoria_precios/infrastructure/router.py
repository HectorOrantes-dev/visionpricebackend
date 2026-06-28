"""Router de auditoría de precios — EXCLUSIVO del ingeniero civil."""
from fastapi import APIRouter, Depends, Query

from src.features.auditoria_precios.application.auditar import (
    AuditarPresupuesto,
    AuditarZona,
    AuditarZonaQuery,
    ResultadoAuditoria,
)
from src.features.auditoria_precios.infrastructure.dependencies import (
    get_auditar_presupuesto,
    get_auditar_zona,
)
from src.features.auditoria_precios.infrastructure.schemas import AuditoriaOut
from src.oauth.dependencies import CurrentUser
from src.oauth.permisos import Permisos
from src.oauth.roles import require_roles

solo_ingeniero = require_roles(*Permisos.AUDITORIA_PRECIOS)

router = APIRouter(prefix="/auditoria/precios", tags=["auditoria-precios"])


def _to_out(res: ResultadoAuditoria) -> AuditoriaOut:
    return AuditoriaOut(
        total=res.total,
        anomalias=res.anomalias,
        lineas=[
            {
                "detalle_id": ln.detalle_id,
                "presupuesto_id": ln.presupuesto_id,
                "material_id": ln.material_id,
                "descripcion": ln.descripcion,
                "precio_unitario": ln.precio_unitario,
                "analisis": {
                    "n_historico": ln.analisis.n_historico,
                    "mediana": ln.analisis.mediana,
                    "es_anomalia": ln.analisis.es_anomalia,
                    "severidad": ln.analisis.severidad,
                    "razones": ln.analisis.razones,
                    "limite_inferior": ln.analisis.limite_inferior,
                    "limite_superior": ln.analisis.limite_superior,
                },
            }
            for ln in res.lineas
        ],
    )


@router.get(
    "/presupuestos/{presupuesto_id}",
    response_model=AuditoriaOut,
    summary="Auditar las líneas de un presupuesto contra el histórico de su zona",
)
async def auditar_presupuesto(
    presupuesto_id: int,
    _: CurrentUser = Depends(solo_ingeniero),
    use_case: AuditarPresupuesto = Depends(get_auditar_presupuesto),
) -> AuditoriaOut:
    return _to_out(await use_case.execute(presupuesto_id))


@router.get(
    "/anomalias",
    response_model=AuditoriaOut,
    summary="Escanear una zona (lat/lng) y devolver las líneas anómalas",
)
async def anomalias_en_zona(
    lat: float = Query(...),
    lng: float = Query(...),
    _: CurrentUser = Depends(solo_ingeniero),
    use_case: AuditarZona = Depends(get_auditar_zona),
) -> AuditoriaOut:
    return _to_out(await use_case.execute(AuditarZonaQuery(lat=lat, lng=lng)))
