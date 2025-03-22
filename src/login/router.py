from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.settings import settings
from src.users.models import User

from .schemas import Token

router = APIRouter()


# Функция для получения пользователя из базы
async def get_user_by_email(
    email: str, session: AsyncSession = Depends(get_async_session)
):
    query = select(User).where(User.email == email)
    result = await session.execute(query)
    user = result.scalars().first()
    return user


# Функция для аутентификации
async def authenticate_user(
    email: str,
    password: str,
    session: AsyncSession = Depends(get_async_session),
):
    user = await get_user_by_email(email, session)
    if not user:
        return False
    if not user.check_password(password):
        return False
    return user


# Функция для создания токена
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


# Эндпоинт для получения токена
@router.post("/login/", response_model=Token)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_async_session),
):
    user = await authenticate_user(
        form_data.username, form_data.password, session
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,  # Доступен только для сервера
        secure=True,  # Использовать только по HTTPS
        samesite="Lax",  # Политика SameSite
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Время жизни
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout/")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}
