import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.charge import Charge, ChargeStatus
from app.rules.charge_rules import check_duplicate
from app.schemas.charge import ChargeCreate, ChargeResponse, ChargeStatusResponse
from app.workers.charge_worker import process_charge

router = APIRouter(prefix="/charges", tags=["charges"])


@router.post("/", response_model=ChargeResponse, status_code=status.HTTP_202_ACCEPTED)
def create_charge(payload: ChargeCreate, db: Session = Depends(get_db)):
    """
    Envia uma cobrança para processamento assíncrono.
    Usa idempotency_key para evitar cobranças duplicadas.
    """
    existing = check_duplicate(payload.idempotency_key, db)
    if existing:
        return existing  # Isso retorna a cobrança original

    charge = Charge(
        user_id=payload.user_id,
        amount=payload.amount,
        description=payload.description,
        idempotency_key=payload.idempotency_key,
        status=ChargeStatus.PENDING,
    )
    db.add(charge)
    db.commit()
    db.refresh(charge)

    task = process_charge.delay(str(charge.id))
    charge.celery_task_id = task.id
    db.commit()
    db.refresh(charge)

    return charge


@router.get("/{charge_id}", response_model=ChargeStatusResponse)
def get_charge_status(charge_id: uuid.UUID, db: Session = Depends(get_db)):
    """Consulta o status de uma cobrança pelo ID."""
    charge = db.query(Charge).filter(Charge.id == charge_id).first()
    if not charge:
        raise HTTPException(status_code=404, detail="Cobrança não encontrada.")
    return charge


@router.get("/", response_model=list[ChargeResponse])
def list_charges(
    user_id: str | None = None,
    status: ChargeStatus | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Lista cobranças com filtros opcionais por user_id e status."""
    query = db.query(Charge)
    if user_id:
        query = query.filter(Charge.user_id == user_id)
    if status:
        query = query.filter(Charge.status == status)
    return query.order_by(Charge.created_at.desc()).limit(limit).all()
