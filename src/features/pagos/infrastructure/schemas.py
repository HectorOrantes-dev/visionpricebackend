"""Schemas HTTP del webhook de pagos."""
from datetime import datetime

from pydantic import BaseModel, Field


class PagosCallbackRequest(BaseModel):
    """Payload que envía el microservicio de Pagos al cambiar una suscripción.

    Mapea a su modelo SubscriptionOut (user_id, plan_key, status, period end).
    """

    user_id: int
    plan_key: str = Field(max_length=50)
    status: str = Field(max_length=20)  # pending|active|past_due|cancelled|expired
    current_period_end: datetime | None = None


class PagosCallbackResponse(BaseModel):
    received: bool = True
    user_id: int
