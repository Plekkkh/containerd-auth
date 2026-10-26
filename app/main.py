from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.config import Settings
from app.db import init_db
from app.auth.bootstrap import ensure_bootstrap_admin
from app.runtime.factory import make_runtime
from app.routers import auth, containers, images, admin

settings = Settings()


def create_app() -> FastAPI:
    init_db(settings.APP_DB_URL or settings.APP_DB_PATH)
    ensure_bootstrap_admin(settings)

    app = FastAPI(title="Container Manager", version="1.0.0")
    app.state.settings = settings
    app.state.runtime = make_runtime(settings)

    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(containers.router, prefix="/containers", tags=["containers"])
    app.include_router(images.router, prefix="/images", tags=["images"])
    app.include_router(admin.router, prefix="/admin", tags=["admin"])

    return app


app = create_app()


@app.middleware("http")
async def security_headers(request, call_next):
    try:
        response = await call_next(request)
    except Exception:
        response = JSONResponse({"detail": "Internal Server Error"}, status_code=500)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' cdn.jsdelivr.net 'unsafe-inline' blob:; "
        "style-src 'self' cdn.jsdelivr.net 'unsafe-inline'; "
        "img-src 'self' data: https://fastapi.tiangolo.com; "
        "font-src cdn.jsdelivr.net; "
        "worker-src 'self' blob:; "
        "connect-src 'self' cdn.jsdelivr.net"
    )
    response.headers["Permissions-Policy"] = "none"
    response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.APP_HOST, port=settings.APP_PORT)