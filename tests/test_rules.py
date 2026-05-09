"""
Testes unitários das regras de negócio.
Não precisam de banco de dados real, usam mocks.
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.rules.charge_rules import (
    RuleViolation,
    check_business_hours,
    check_daily_limit,
    check_minimum_amount,
    run_all_rules,
)


class TestCheckBusinessHours:
    def test_dentro_do_horario(self):
        now = datetime(2024, 1, 15, 10, 0)  # 10h
        check_business_hours(now)  # não deve levantar

    def test_antes_do_horario(self):
        now = datetime(2024, 1, 15, 7, 59)
        with pytest.raises(RuleViolation, match="horário"):
            check_business_hours(now)

    def test_apos_o_horario(self):
        now = datetime(2024, 1, 15, 20, 0)
        with pytest.raises(RuleViolation, match="horário"):
            check_business_hours(now)

    def test_exatamente_no_inicio(self):
        now = datetime(2024, 1, 15, 8, 0)
        check_business_hours(now)  # deve passar


class TestCheckMinimumAmount:
    def test_valor_valido(self):
        check_minimum_amount(Decimal("1.00"))

    def test_valor_minimo_exato(self):
        check_minimum_amount(Decimal("0.50"))

    def test_valor_abaixo_do_minimo(self):
        with pytest.raises(RuleViolation, match="mínimo"):
            check_minimum_amount(Decimal("0.49"))


class TestCheckDailyLimit:
    def test_dentro_do_limite(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.scalar.return_value = Decimal("100.00")

        # 100 existente + 200 novo = 300, dentro do limite de 50000
        check_daily_limit("user_1", Decimal("200.00"), db)

    def test_ultrapassa_limite(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.scalar.return_value = Decimal("49900.00")

        with pytest.raises(RuleViolation, match="Limite diário"):
            check_daily_limit("user_1", Decimal("200.00"), db)

    def test_sem_cobranças_anteriores(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.scalar.return_value = None

        check_daily_limit("user_novo", Decimal("1000.00"), db)


class TestRunAllRules:
    def test_todas_as_regras_passam(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.scalar.return_value = Decimal("0")
        now = datetime(2024, 1, 15, 10, 0)

        run_all_rules("user_1", Decimal("100.00"), db, now=now)

    def test_falha_no_horario(self):
        db = MagicMock()
        now = datetime(2024, 1, 15, 6, 0)

        with pytest.raises(RuleViolation):
            run_all_rules("user_1", Decimal("100.00"), db, now=now)
