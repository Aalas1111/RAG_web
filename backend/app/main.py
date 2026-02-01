"""FastAPI 主应用"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings, ensure_dirs
from app.database import init_db
from app.routers import api, admin

ensure_dirs()
init_db()

app = FastAPI(title="LightRAG Web API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router, prefix="/api", tags=["api"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.get("/")
def root():
    return {"message": "LightRAG Web API", "docs": "/docs"}
