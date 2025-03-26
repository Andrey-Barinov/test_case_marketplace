from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Category


async def test_post_categories_protect(async_client: AsyncClient):
    response = await async_client.post(
        "/categories/",
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Отсутствует токен доступа"


async def test_create_category(
    authenticated_client, test_session: AsyncSession
):
    response = await authenticated_client.post(
        "/categories/", json={"title": "test_category1"}
    )
    assert response.status_code == 200

    query = select(Category).where(Category.title == "test_category1")
    result = await test_session.execute(query)
    category = result.scalar_one_or_none()

    assert category.title == "test_category1"


async def test_create_category_with_protect_from_duplication(
    authenticated_client,
):
    response = await authenticated_client.post(
        "/categories/", json={"title": "test_category1"}
    )
    assert response.status_code == 400
    detail = "Категория с таким названием test_category1 уже существует!"
    assert response.json()["detail"] == detail
