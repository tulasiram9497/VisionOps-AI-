from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.core.logging import logger
from app.database.database import create_db_and_tables
from app.vision.runtime import runtime


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()
    runtime.start()
    logger.info("VisionOps AI backend started.")
    yield
    runtime.stop()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "VisionOps AI backend is running."}
