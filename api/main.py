from __future__ import annotations

from fastapi import FastAPI

from api.routers.verify import router as verify_router
from config.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="FakeScope Agent",
        description="LangGraph-powered fake news verification agent",
        version="0.1.0",
        swagger_ui_parameters={"displayRequestDuration": True},
    )

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(verify_router)

    @app.on_event("startup")
    async def on_startup() -> None:  # pragma: no cover
        _ = settings  # ensure settings initialized

    return app


app = create_app()


__all__ = ["app", "create_app"]
