from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.auth import router as auth_router
from app.api.routes.vault import router as vault_router
from app.core.database import get_db


app = FastAPI(
    title="Password Manager API",
    version="1.0.0",
)


app.include_router(auth_router)
app.include_router(vault_router)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "password-manager",
        "message": "Password Manager API is running",
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "password-manager",
    }


@app.get("/health/db")
async def database_health(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "database": result.scalar(),
    }