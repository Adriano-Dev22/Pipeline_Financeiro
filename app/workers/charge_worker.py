"""
Worker de processamento de cobranças.
Implementa retry com backoff exponencial + jitter e dead-letter queue.
"""

import random
import uuid
from datetime import datetime

from celery import Task
from celery.utils.log import get_task_logger

from app.celery_app import celery_app
from app.config import settings
from app.database import SessionLocal
from app.models.charge import Charge, ChargeStatus
from app.rules.charge_rules import RuleViolation, run_all_rules

logger = get_task_logger(__name__)


def _exponential_backoff(retry: int, base: float = 2.0, cap: float = 300.0) -> float:
    """Backoff exponencial com jitter para evitar thundering herd."""
    delay = min(base ** retry, cap)
    jitter = random.uniform(0, delay * 0.2)
    return delay + jitter


class ChargeTask(Task):
    """Task base com acesso ao DB e lógica de falha centralizada."""

    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        charge_id = kwargs.get("charge_id") or (args[0] if args else None)
        if not charge_id:
            return

        db = SessionLocal()
        try:
            charge = db.query(Charge).filter(Charge.id == uuid.UUID(str(charge_id))).first()
            if charge:
                charge.status = ChargeStatus.DEAD_LETTER
                charge.error_message = str(exc)
                db.commit()
                logger.error(f"[DEAD-LETTER] Charge {charge_id} → {exc}")
        finally:
            db.close()


@celery_app.task(
    bind=True,
    base=ChargeTask,
    name="app.workers.charge_worker.process_charge",
    max_retries=settings.max_retry_attempts,
    queue="charges",
)
def process_charge(self, charge_id: str) -> dict:
    db = SessionLocal()
    try:
        charge = db.query(Charge).filter(Charge.id == uuid.UUID(charge_id)).first()
        if not charge:
            raise ValueError(f"Charge {charge_id} não encontrada.")

        charge.status = ChargeStatus.PROCESSING
        db.commit()

        # Valida regras de negócio dentro do worker (idempotente)
        run_all_rules(user_id=charge.user_id, amount=charge.amount, db=db)

        # ---- Aqui entraria a chamada ao gateway de pagamento real ----
        # Ex: result = payment_gateway.charge(charge.amount, charge.user_id)
        # Simulamos sucesso após validação das regras.

        charge.status = ChargeStatus.COMPLETED
        charge.processed_at = datetime.utcnow()
        db.commit()

        logger.info(f"[OK] Charge {charge_id} processada com sucesso.")
        return {"charge_id": charge_id, "status": "completed"}

    except RuleViolation as exc:
        # Regra de negócio violada → falha permanente, sem retry
        charge.status = ChargeStatus.FAILED
        charge.error_message = str(exc)
        db.commit()
        logger.warning(f"[RULE] Charge {charge_id} rejeitada: {exc}")
        return {"charge_id": charge_id, "status": "failed", "reason": str(exc)}

    except Exception as exc:
        charge.retry_count += 1
        charge.error_message = str(exc)
        db.commit()

        countdown = _exponential_backoff(self.request.retries)
        logger.warning(
            f"[RETRY {self.request.retries + 1}/{settings.max_retry_attempts}] "
            f"Charge {charge_id} → retry em {countdown:.1f}s. Erro: {exc}"
        )
        raise self.retry(exc=exc, countdown=countdown)

    finally:
        db.close()
