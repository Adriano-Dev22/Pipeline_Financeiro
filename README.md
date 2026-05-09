# AsyncLedger 🏦

Pipeline assíncrono de processamento de cobranças financeiras construído com **FastAPI**, **Celery** e **Redis**.

## Arquitetura

```
Cliente → FastAPI → PostgreSQL (persiste) → Celery (fila) → Worker → [gateway]
                                                    ↓
                                            Dead-Letter Queue (falhas permanentes)
```

## Funcionalidades

- ✅ **Processamento assíncrono** com Celery + Redis
- 🔁 **Retry com backoff exponencial + jitter** (evita thundering herd)
- ☠️ **Dead-letter queue** para falhas permanentes
- 📋 **Regras de negócio** — limite diário, horário útil, valor mínimo
- 🔑 **Idempotência** via `idempotency_key` (sem cobranças duplicadas)
- 📊 **Dashboard** de workers com Flower
- 🧪 **Testes unitários** das regras de negócio

## Stack

| Camada | Tecnologia |
|--------|-----------|
| API | FastAPI + Uvicorn |
| Fila | Celery + Redis |
| Banco | PostgreSQL + SQLAlchemy |
| Dashboard | Flower |
| Testes | Pytest |
| Infra | Docker Compose |

## Como rodar

```bash
# 1. Clone e configure
cp .env.example .env

# 2. Suba os serviços
docker compose up --build

# 3. Acesse
# API Docs:  http://localhost:8000/docs
# Flower:    http://localhost:5555
```

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/charges/` | Criar cobrança (retorna 202) |
| `GET` | `/charges/{id}` | Consultar status |
| `GET` | `/charges/?user_id=X` | Listar cobranças |
| `GET` | `/health` | Health check |

## Exemplo de uso

```bash
curl -X POST http://localhost:8000/charges/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "usr_123",
    "amount": 150.00,
    "description": "Assinatura mensal",
    "idempotency_key": "order-2024-01-abc"
  }'
```

## Rodando os testes

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Regras de negócio

| Regra | Detalhe |
|-------|---------|
| Horário útil | 08h – 20h (configurável) |
| Limite diário | R$ 50.000,00 por usuário |
| Valor mínimo | R$ 0,50 |
| Retry máximo | 3 tentativas com backoff |
| Idempotência | Via `idempotency_key` única |
