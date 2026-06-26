"""Router del webhook de pagos (interno, X-Api-Key)."""
from fastapi import APIRouter, Depends

from src.features.pagos.application.actualizar_entitlement import (
    ActualizarEntitlement,
    EntitlementCommand,
)
from src.features.pagos.infrastructure.dependencies import (
    get_actualizar_entitlement,
)
from src.features.pagos.infrastructure.schemas import (
    PagosCallbackRequest,
    PagosCallbackResponse,
)
from src.oauth.internal import require_internal_key

router = APIRouter(tags=["pagos"])


@router.post(
    "/pagos/callback",
    response_model=PagosCallbackResponse,
    dependencies=[Depends(require_internal_key)],
    summary="Webhook: el microservicio de Pagos sincroniza el plan del usuario",
)
async def pagos_callback(
    body: PagosCallbackRequest,
    use_case: ActualizarEntitlement = Depends(get_actualizar_entitlement),
) -> PagosCallbackResponse:
    await use_case.execute(
        EntitlementCommand(
            user_id=body.user_id,
            plan_key=body.plan_key,
            status=body.status,
            current_period_end=body.current_period_end,
        )
    )
    return PagosCallbackResponse(received=True, user_id=body.user_id)
