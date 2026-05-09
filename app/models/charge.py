import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, String, Numeric, DateTime, Integer, Text, Enum
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base



class ChargeStatus(str, PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class Charge(Base):
    __tablename__ = "charges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(64), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    description = Column(String(255), nullable=False)
    idempotency_key = Column(String(128), unique=True, nullable=False)
    status = Column(Enum(ChargeStatus), default=ChargeStatus.PENDING, nullable=False)
    retry_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    celery_task_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
