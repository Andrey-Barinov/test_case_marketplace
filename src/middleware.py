from fastapi import Request, status
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .settings import settings


class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Расширенный список исключений
        excluded_paths = [
            "/users/registration/",
            "/users/registration",
            "/login/",
            "/login",
            "/docs/",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/redoc/",
            "/favicon.ico",
        ]

        # Проверка, начинается ли путь с одного из исключений
        if any(request.url.path == path for path in excluded_paths):
            return await call_next(request)

        token = request.cookies.get("access_token")
        if not token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing access token"},
            )

        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            request.state.user = payload["sub"]
        except JWTError:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Invalid or expired token"},
            )

        return await call_next(request)
