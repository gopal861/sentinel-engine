from fastapi import FastAPI
from sentinel.api.routes import router as sentinel_router


app = FastAPI(
    title="Sentinel Engine",
    version="V1 - Strict Governance Mode",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(sentinel_router)
