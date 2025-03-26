from math import ceil
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
)
from sqlalchemy import delete, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.categories.models import Category
from src.database import get_async_session

from .models import Article, DeletedArticle
from .schemas import ArticleCreate, ArticleResponse
from .utils import delete_image_from_s3, upload_image_to_s3
from .validators import ImageValidator

router = APIRouter(prefix="/articles", tags=["Articles"])


MAX_PAGE_SIZE = 50
DEFAULT_PAGE_SIZE = 10


@router.get("/", response_model=List[ArticleResponse])
async def get_articles(
    session: AsyncSession = Depends(get_async_session),
    search: Optional[str] = Query(
        None, description="Поиск по заголовку и содержимому"
    ),
    category_id: Optional[int] = Query(None, description="Фильтр по категории"),
    page_number: int = Query(
        1, ge=1, description="Номер страницы (начиная с 1)"
    ),
    page_size: int = Query(
        DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description="Количество элементов на странице",
    ),
):
    """Эндпоинт получения списка статей с поддержкой поиска,
    фильтрации и пагинации."""

    # Базовый запрос
    query = select(Article)

    # Полнотекстовый поиск
    if search:
        search_query = func.plainto_tsquery("russian", search)
        query = query.where(
            func.to_tsvector(
                "russian", Article.title + " " + Article.content
            ).op("@@")(search_query)
        )

    # Фильтрация по категории
    if category_id:
        query = query.where(Article.category_id == category_id)

    # Получаем общее количество статей для пагинации
    count_query = select(func.count()).select_from(query.subquery())
    total_count = (await session.execute(count_query)).scalar()

    # Вычисляем общее количество страниц
    total_pages = ceil(total_count / page_size) if total_count > 0 else 1

    # Проверяем, не выходит ли page_number за пределы
    if page_number > total_pages:
        raise HTTPException(status_code=404, detail="Страница не найдена")

    # Применяем пагинацию
    query = query.limit(page_size).offset((page_number - 1) * page_size)

    # Выполняем запрос
    result = await session.execute(query)
    articles = result.scalars().all()

    return articles


@router.post("/", response_model=ArticleResponse)
async def create_article(
    new_article: ArticleCreate = Depends(ArticleCreate.as_form),
    image: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session),
):
    title_query = select(Article).where(Article.title == new_article.title)
    title = await session.execute(title_query)
    if title.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Статья с таким названием"
            f" {new_article.title} уже существует!",
        )

    await ImageValidator.validate_image(image)

    category_id_query = select(Category).where(
        Category.id == new_article.category_id
    )
    category_id_query = await session.execute(category_id_query)
    if not category_id_query.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Категория с id {new_article.category_id} не существует!",
        )

    # Загружаем изображение в MinIO
    image_url = await upload_image_to_s3(image)

    db_new_article = Article(
        title=new_article.title,
        content=new_article.content,
        category_id=new_article.category_id,
        image_url=image_url,
    )

    session.add(db_new_article)
    await session.commit()
    await session.refresh(db_new_article)

    return db_new_article


@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: int,
    updated_article: ArticleCreate = Depends(ArticleCreate.as_form),
    image: Optional[UploadFile] = File(None),
    session: AsyncSession = Depends(get_async_session),
):
    # Проверяем, существует ли статья
    query = select(Article).where(Article.id == article_id)
    result = await session.execute(query)
    db_article = result.scalar_one_or_none()

    if not db_article:
        raise HTTPException(status_code=404, detail="Статья не найдена")

    # Проверяем, существует ли категория
    category_query = select(Category).where(
        Category.id == updated_article.category_id
    )
    category_result = await session.execute(category_query)
    if not category_result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Категория с id "
            f"{updated_article.category_id} не существует!",
        )

    if image:
        await ImageValidator.validate_image(image)

        # Удаляем старое изображение
        try:
            await delete_image_from_s3(db_article.image_url)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка удаления старого изображения: {str(e)}",
            )

        # Загружаем новое изображение
        try:
            image_url = await upload_image_to_s3(image)
            db_article.image_url = image_url
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Ошибка загрузки изображения: {str(e)}"
            )

    db_article.title = updated_article.title
    db_article.content = updated_article.content
    db_article.category_id = updated_article.category_id

    try:
        session.add(db_article)
        await session.commit()
        await session.refresh(db_article)

        return db_article
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Ошибка обновления статьи: {str(e)}"
        )


@router.delete("/{id}")
async def delete_article_from_table_articles_insert_into_table_deleted_articles(
    id: int, session: AsyncSession = Depends(get_async_session)
):
    query = select(Article).where(Article.id == id)
    result = await session.execute(query)
    db_article = result.scalars().first()

    if db_article is None:
        raise HTTPException(status_code=404, detail="Статья не найдена!")

    article_data = {
        "title": db_article.title,
        "content": db_article.content,
        "category_id": db_article.category_id,
        "image_url": db_article.image_url,
    }

    delete_stmt = delete(Article).where(Article.id == id)

    insert_stmt = insert(DeletedArticle).values(**article_data)

    await session.execute(delete_stmt)
    await session.execute(insert_stmt)
    await session.commit()

    return {"detail": "Статья удалена!"}
