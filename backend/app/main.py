from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from . import config
from .routers import api
from .services import history
from .services.detector import detector

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s: %(message)s")

@asynccontextmanager
async def lifespan(_: FastAPI):
    history.init_db()
    detector.load()
    yield

app = FastAPI(title="Kelasku API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router)
app.mount("/files/uploads", StaticFiles(directory=config.UPLOAD_DIR), name="uploads")
app.mount("/files/results", StaticFiles(directory=config.RESULT_DIR), name="results")

@app.get("/")
def root():
    return {"app": "Kelasku API", "docs": "/docs", "health": "/api/health"}