from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routers import (
    user, chat, thread, message, recipe
)
from app.core.config import settings
from app.core.openapi import custom_openapi


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        openapi_url=f"{settings.api_v1_str}/openapi.json",
        docs_url=f"{settings.api_v1_str}/docs",
        swagger_ui_init_oauth={
            "clientId": settings.auth0_client_id,
            "usePkceWithAuthorizationCodeGrant": True,
            "redirectUrl": f"{settings.api_v1_str}/docs/oauth2-redirect",
            "additionalQueryStringParams": {
                "audience": settings.auth0_api_audience,
                "scope": "openid profile email",
            },
            "scopeSeparator": " ",
        },
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backends_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
   
    app.include_router(
        user.router,
        prefix=f"{settings.api_v1_str}/user",
        tags=["user"],
    )
    app.include_router(
        chat.router,
        prefix=f"{settings.api_v1_str}/chat",
        tags=["chat"],
    )
    app.include_router(
        thread.router,
        prefix=f"{settings.api_v1_str}/thread",
        tags=["thread"],
    )
    app.include_router(
        message.router,
        prefix=f"{settings.api_v1_str}/message",
        tags=["message"],
    )
    app.include_router(
        recipe.router,
        prefix=f"{settings.api_v1_str}/recipes",
        tags=["recipes"],
    )

    return app


# Instantiate
app = create_app()
