from datetime import datetime, timezone

from fastapi import FastAPI

from app.api.routes import audit, auth, dashboard, requests, services
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.schemas.common import HealthResponse

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")

register_exception_handlers(app)

app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(services.router, prefix=settings.api_v1_prefix)
app.include_router(requests.router, prefix=settings.api_v1_prefix)
app.include_router(audit.router, prefix=settings.api_v1_prefix)
app.include_router(dashboard.router, prefix=settings.api_v1_prefix)


@app.get(f"{settings.api_v1_prefix}/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", timestamp=datetime.now(timezone.utc))
