import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from alembic import command
from alembic.config import Config
from src.main import app  # Импортируем приложение FastAPI
from src.users.models import User  # Импортируем модель пользователя

from .database import get_async_session
from .database_test import get_test_async_session
from .settings import test_settings

app.dependency_overrides[get_async_session] = get_test_async_session


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    # Применяем миграции
    alembic_config = Config("alembic.ini")
    alembic_config.set_main_option(
        "sqlalchemy.url", test_settings.TEST_ALEMBIC_DATABASE_URL
    )
    command.upgrade(alembic_config, "head")


# Фикстура для создания тестового пользователя
@pytest.fixture(scope="session")
async def test_user():
    async for session in get_test_async_session():
        password = "testpassword"
        db_user = User(
            email="example@mail.ru",
            phone_number="+79991112233",
            name="Test_name",
        )

        db_user.set_password(password)
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
        return db_user


@pytest.fixture
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://127.0.0.1",
        follow_redirects=True,
    ) as ac:
        yield ac
