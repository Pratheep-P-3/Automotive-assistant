from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI

from backend.routes.diagnose import router as diagnose_router

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

app = FastAPI(
    title="Automotive Vehicle Diagnostics and Service Recommendation Assistant",
    version="1.0.0",
)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(diagnose_router)
