from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.backend.api.router import api_router
from src.backend.core.config import get_settings
from src.backend.domain.common.errors import AuthenticationError, DomainError
from src.backend.infrastructure.db.session import close_db, init_db
from src.backend.security.rate_limit import ChatRateLimitMiddleware


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    if settings.auto_create_tables:
        await init_db()
    yield
    await close_db()


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    description="Resident handbook Q&A and ticket management backend",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ChatRateLimitMiddleware)
app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(DomainError)
async def handle_domain_error(_request: Request, exc: DomainError) -> JSONResponse:
    headers = {"WWW-Authenticate": "Bearer"} if isinstance(exc, AuthenticationError) else None
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
        headers=headers,
    )


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "env": settings.app_env}
