"""
Regras de negócio para processamento de cobranças.
Cada regra é uma função pura, fácil de testar e estender.
"""

from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.models.charge import Charge, ChargeStatus


class RuleViolation(Exception):
    """Levantada quando uma cobrança viola uma regra de negócio."""
    pass


def check_business_hours(now: datetime | None = None) -> None:
    """Cobranças só são aceitas dentro do horário útil."""
    now = now or datetime.now()
    hour = now.hour
    if not (settings.business_hours_start <= hour < settings.business_hours_end):
        raise RuleViolation(
            f"Cobranças só são processadas entre "
            f"{settings.business_hours_start}h e {settings.business_hours_end}h."
        )


def check_daily_limit(user_id: str, amount: Decimal, db: Session) -> None:
    """Usuário não pode ultrapassar o limite diário configurado."""
    today_start = datetime.combine(date.today(), datetime.min.time())

    daily_total = db.query(func.sum(Charge.amount)).filter(
        Charge.user_id == user_id,
        Charge.status == ChargeStatus.COMPLETED,
        Charge.processed_at >= today_start,
    ).scalar() or Decimal("0")

    if daily_total + amount > Decimal(str(settings.daily_limit_brl)):
        raise RuleViolation(
            f"Limite diário de R$ {settings.daily_limit_brl:,.2f} atingido. "
            f"Total hoje: R$ {daily_total:,.2f}."
        )


def check_duplicate(idempotency_key: str, db: Session) -> Charge | None:
    """
    Detecta cobranças duplicadas pela idempotency_key.
    Retorna a cobrança existente se for duplicata, None caso contrário.
    """
    return db.query(Charge).filter(
        Charge.idempotency_key == idempotency_key
    ).first()


def check_minimum_amount(amount: Decimal) -> None:
    """Valor mínimo de R$ 0,50 (padrão comum em gateways de pagamento)."""
    if amount < Decimal("0.50"):
        raise RuleViolation("Valor mínimo para cobrança é R$ 0,50.")


def run_all_rules(
    user_id: str,
    amount: Decimal,
    db: Session,
    now: datetime | None = None,
) -> None:
    """Executa todas as regras em sequência. Levanta RuleViolation na primeira falha."""
    check_minimum_amount(amount)
    check_business_hours(now)
    check_daily_limit(user_id, amount, db)
