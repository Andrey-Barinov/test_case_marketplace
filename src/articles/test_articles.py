from io import BytesIO
from unittest.mock import AsyncMock

from httpx import AsyncClient
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.categories.models import Category

from .models import Article, DeletedArticle


async def test_get_articles_protect(async_client: AsyncClient):
    response = await async_client.post(
        "/articles/",
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Отсутствует токен доступа"


async def test_create_article(
    mocker: AsyncMock,
    authenticated_client: AsyncClient,
    test_session: AsyncSession,
):
    mock_upload_image = mocker.patch("src.articles.router.upload_image_to_s3")

    # Настраиваем возврат значения (поддельный URL изображения)
    mock_upload_image.return_value = "https://fake-s3-url.com/image.jpg"

    new_article_data = {
        "title": "Test Article",
        "content": "This is a test article.",
        "category_id": 1,
    }

    # Создаём файл
    file_content = BytesIO(b"fake image content")

    response = await authenticated_client.post(
        "/articles/",
        data=new_article_data,
        files={"image": ("test_image.jpg", file_content, "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.json()["image_url"] == "https://fake-s3-url.com/image.jpg"

    query = select(Article).where(Article.title == "Test Article")
    result = await test_session.execute(query)
    new_article = result.scalar_one_or_none()

    assert new_article.content == "This is a test article."


async def test_create_article_protect_from_title_duplication(
    authenticated_client: AsyncClient,
):
    new_article_data_same_title = {
        "title": "Test Article",
        "content": "This is a test article.",
        "category_id": 1,
    }

    # Создаём файл
    file_content = BytesIO(b"fake image content")

    response = await authenticated_client.post(
        "/articles/",
        data=new_article_data_same_title,
        files={"image": ("test_image.jpg", file_content, "image/jpeg")},
    )
    assert response.status_code == 400
    detail = "Статья с таким названием Test Article уже существует!"
    assert response.json()["detail"] == detail


async def test_create_article_protect_from_wrong_id_category(
    authenticated_client: AsyncClient,
):
    new_article_data_same_title = {
        "title": "Test Article1",
        "content": "This is a test article.",
        "category_id": 4,
    }

    # Создаём файл
    file_content = BytesIO(b"fake image content")

    response = await authenticated_client.post(
        "/articles/",
        data=new_article_data_same_title,
        files={"image": ("test_image.jpg", file_content, "image/jpeg")},
    )
    assert response.status_code == 400
    detail = "Категория с id 4 не существует!"
    assert response.json()["detail"] == detail


async def test_get_all_articles(
    authenticated_client: AsyncClient,
    test_category: Category,
    test_session: AsyncSession,
):
    # Создаём уникальные тестовые статьи
    articles = [
        {
            "title": "Unique Article 1",
            "content": "Content 1",
            "category_id": test_category.id,
        },
        {
            "title": "Unique Article 2",
            "content": "Content 2",
            "category_id": test_category.id,
        },
    ]

    await test_session.execute(insert(Article), articles)
    await test_session.commit()

    # Делаем запрос на получение всех статей
    response = await authenticated_client.get("/articles/")
    assert response.status_code == 200

    # Проверяем, что статьи с уникальными заголовками присутствуют в ответе
    response_data = response.json()
    titles = [article["title"] for article in response_data]

    assert "Unique Article 1" in titles
    assert "Unique Article 2" in titles


async def test_filter_articles_by_category(
    authenticated_client: AsyncClient,
    test_category: Category,
    test_session: AsyncSession,
):
    # Создаём тестовую категорию и статьи
    other_category = Category(title="Other Category")
    test_session.add(other_category)
    await test_session.commit()

    articles = [
        {
            "title": "Unique Article 3",
            "content": "Content 3",
            "category_id": test_category.id,
        },
        {
            "title": "Unique Article 4",
            "content": "Content 4",
            "category_id": other_category.id,
        },
    ]

    await test_session.execute(insert(Article), articles)
    await test_session.commit()

    # Фильтруем статьи по категории test_category
    response = await authenticated_client.get(
        f"/articles/?category_id={test_category.id}"
    )
    assert response.status_code == 200

    # Проверяем, что в ответе есть только статья из test_category
    response_data = response.json()
    titles = [article["title"] for article in response_data]

    assert "Unique Article 3" in titles
    assert "Unique Article 4" not in titles


async def test_search_articles(
    authenticated_client: AsyncClient,
    test_category: Category,
    test_session: AsyncSession,
):
    # Создаём уникальные тестовые статьи
    articles = [
        {
            "title": "Python Unique Article",
            "content": "Learn Python",
            "category_id": test_category.id,
        },
        {
            "title": "Django Unique Guide",
            "content": "Learn Django",
            "category_id": test_category.id,
        },
    ]

    await test_session.execute(insert(Article), articles)
    await test_session.commit()

    # Поиск статьи с ключевым словом "Python"
    response = await authenticated_client.get("/articles/?search=Python")
    assert response.status_code == 200

    # Проверяем, что вернулась только статья про Python
    response_data = response.json()
    titles = [article["title"] for article in response_data]

    assert "Python Unique Article" in titles
    assert "Django Unique Guide" not in titles


async def test_pagination(
    authenticated_client: AsyncClient,
    test_category: Category,
    test_session: AsyncSession,
):
    # Создаём 15 уникальных тестовых статей
    articles = [
        {
            "title": f"Paginated Article {i}",
            "content": f"Content {i}",
            "category_id": test_category.id,
        }
        for i in range(1, 16)
    ]

    await test_session.execute(insert(Article), articles)
    await test_session.commit()

    # Проверяем первую страницу (по умолчанию page_size = 10)
    response = await authenticated_client.get(
        "/articles/?page_number=1&page_size=10"
    )
    assert response.status_code == 200
    response_data = response.json()

    # Проверяем, что вернулись только первые 10 статей
    assert len(response_data) == 10
    assert response_data[0]["title"] == "Test Article"
    assert response_data[-1]["title"] == "Paginated Article 3"

    # Проверяем вторую страницу
    response = await authenticated_client.get(
        "/articles/?page_number=2&page_size=10"
    )
    assert response.status_code == 200
    response_data = response.json()

    # Проверяем, что вернулись оставшиеся 10 статей
    assert len(response_data) == 10
    assert response_data[0]["title"] == "Paginated Article 4"
    assert response_data[-1]["title"] == "Paginated Article 13"

    # Проверяем запрос несуществующей страницы
    response = await authenticated_client.get(
        "/articles/?page_number=5&page_size=10"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Страница не найдена"


async def test_invalid_page_size(authenticated_client: AsyncClient):
    # Проверяем, что передача некорректного page_size вызывает ошибку
    response = await authenticated_client.get("/articles/?page_size=0")
    assert response.status_code == 422

    response = await authenticated_client.get(
        "/articles/?page_size=101"
    )  # MAX_PAGE_SIZE = 100
    assert response.status_code == 422


async def test_put_article(
    authenticated_client: AsyncClient, test_session: AsyncSession
):
    new_article_data = {
        "title": "Changed Article",
        "content": "Changed content",
        "category_id": 1,
    }

    response = await authenticated_client.put(
        "/articles/1", data=new_article_data
    )

    assert response.status_code == 200
    query = select(Article).where(Article.title == "Changed Article")
    result = await test_session.execute(query)
    changed_article = result.scalar_one_or_none()

    assert changed_article.content == "Changed content"


async def test_put_article_protect_from_wrong_id_category(
    authenticated_client: AsyncClient,
):
    changed_article_data_with_wrong_id_category = {
        "title": "Changed Article",
        "content": "Changed content",
        "category_id": 4,
    }

    response = await authenticated_client.put(
        "/articles/1",
        data=changed_article_data_with_wrong_id_category,
    )
    assert response.status_code == 400
    detail = "Категория с id 4 не существует!"
    assert response.json()["detail"] == detail


async def test_delete_article(
    authenticated_client: AsyncClient, test_session: AsyncSession
):
    response = await authenticated_client.delete("/articles/1")
    print(response.text)
    assert response.status_code == 200

    query1 = select(Article).where(Article.title == "Changed Article")
    result1 = await test_session.execute(query1)
    deleted_article_from_articles = result1.scalar_one_or_none()
    assert deleted_article_from_articles is None

    query2 = select(DeletedArticle).where(
        DeletedArticle.title == "Changed Article"
    )
    result2 = await test_session.execute(query2)
    deleted_article_from_deleted_articles = result2.scalar_one_or_none()

    assert deleted_article_from_deleted_articles.content == "Changed content"


async def test_delete_nonexistent_article(authenticated_client: AsyncClient):
    response = await authenticated_client.delete("/articles/25")

    assert response.status_code == 404

    assert response.json()["detail"] == "Статья не найдена!"
