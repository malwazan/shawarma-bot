import wireup.integration.fastapi
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.calls.endpoints import router as calls_router
from src.config import settings
from src.containers import create_container
from src.livekit.endpoints import router as livekit_router
from src.logfire import configure_logfire, instrument_fastapi, instrument_httpx
from src.user.endpoints import router as user_router
from src.user.middleware import AuthMiddleware
from src.voice.endpoints import router as voice_router


def create_app() -> FastAPI:
    configure_logfire()
    instrument_httpx()

    app = FastAPI(title="Shawarma Bot API")
    instrument_fastapi(app)

    @app.get("")
    @app.get("/health")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(user_router, prefix="/api/v1/users")
    app.include_router(voice_router, prefix="/api/v1/voice")
    app.include_router(livekit_router, prefix="/api/v1/livekit")
    app.include_router(calls_router, prefix="/api/v1/calls")

    # The last middleware added is the outermost:
    # CORS -> Auth -> routes
    app.add_middleware(AuthMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOWED_ORIGINS,
        allow_credentials=True,  # the browser must send the session cookie
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # After all routes are registered: wraps endpoints to resolve Injected[T]
    # and closes the container (disposing the DB engine) on shutdown.
    wireup.integration.fastapi.setup(create_container(), app)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.fastapi:app", host="0.0.0.0", port=4000, reload=settings.DEBUG)
