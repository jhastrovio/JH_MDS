from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.settings import get_settings
from routers.auth import router as auth_router
from routers.market import router as market_router
from routers.health import router as health_router
from routers.diagnostics import router as diagnostics_router
from core.security import get_security_headers

app = FastAPI()
app.include_router(auth_router)
app.include_router(market_router)
app.include_router(health_router)
app.include_router(diagnostics_router)

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="JH Market Data API",
        version="1.0.0",
        description="Real-time market data API with SaxoBank integration",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    # === centralised CORS ===
    origins = settings.get_cors_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # === security headers middleware ===
    @app.middleware("http")
    async def apply_security_headers(request, call_next):
        response = await call_next(request)
        response.headers.update(get_security_headers(settings))
        return response

    # === routers ===
    app.include_router(auth_router)
    app.include_router(market_router)
    app.include_router(health_router)
    if settings.ENV != "production":
        app.include_router(diagnostics_router)

    return app

app = create_app()
