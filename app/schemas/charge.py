import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.models.charge import ChargeStatus


class ChargeCreate(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64)
    amount: Decimal = Field(..., gt=0, le=999999.99)
    description: str = Field(..., min_length=1, max_length=255)
    idempotency_key: str = Field(..., min_length=8, max_length=128)

    @field_validator("amount")
    @classmethod
    def amount_must_have_two_decimals(cls, v):
        return round(v, 2)


class ChargeResponse(BaseModel):
    id: uuid.UUID
    user_id: str
    amount: Decimal
    description: str
    status: ChargeStatus
    retry_count: int
    error_message: str | None
    celery_task_id: str | None
    created_at: datetime
    updated_at: datetime
    processed_at: datetime | None

    model_config = {"from_attributes": True}


class ChargeStatusResponse(BaseModel):
    id: uuid.UUID
    status: ChargeStatus
    retry_count: int
    error_message: str | None
    processed_at: datetime | None

    model_config = {"from_attributes": True}
