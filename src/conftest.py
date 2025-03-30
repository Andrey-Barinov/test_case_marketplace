import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from alembic import command
from alembic.config import Config
from src.categories.models import Category
from src.main import app
from src.users.models import User

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


@pytest.fixture
async def test_session():
    async for session in get_test_async_session():
        yield session


@pytest.fixture(scope="session")
async def test_user():
    """Фикстура для создания тестового пользователя"""
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


@pytest.fixture(scope="session", autouse=True)
async def test_category():
    """Фикстура для создания тестовой категории"""
    async for session in get_test_async_session():
        db_category = Category(
            title="test_category",
        )

        session.add(db_category)
        await session.commit()
        await session.refresh(db_category)
        return db_category


@pytest.fixture
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://127.0.0.1",
        follow_redirects=True,
    ) as ac:
        yield ac


@pytest.fixture(scope="function")
async def authenticated_client(async_client: AsyncClient, test_user: User):
    """Фикстура для аутентифицированного клиента"""
    login_response = await async_client.post(
        "/login/",
        data={"username": test_user.email, "password": "testpassword"},
    )

    assert login_response.status_code == 200
    access_token = login_response.cookies.get("access_token")

    # Убедимся, что токен получен
    assert access_token is not None

    # Устанавливаем этот токен в куки для последующих запросов
    async_client.cookies.set("access_token", access_token)

    return async_client
