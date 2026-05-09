from fastapi import FastAPI

from app.api.charges import router as charges_router
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AsyncLedger",
    description="Pipeline assíncrono de processamento de cobranças financeiras.",
    version="1.0.0",
)

app.include_router(charges_router)


@app.get("/health")
def health():
    return {"status": "ok"}
