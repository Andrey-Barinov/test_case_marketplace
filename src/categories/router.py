from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session

from .models import Category
from .schemas import CategoryCreate, CategoryResponse

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("/", response_model=List[CategoryResponse])
async def get_categories(session: AsyncSession = Depends(get_async_session)):
    query = select(Category)
    result = await session.execute(query)
    return result.scalars().all()


@router.post("/", response_model=CategoryResponse)
async def create_category(
    new_category: CategoryCreate,
    session: AsyncSession = Depends(get_async_session),
):
    title_query = select(Category).where(Category.title == new_category.title)
    title = await session.execute(title_query)
    if title.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Категория с таким названием"
            f" {new_category.title} уже существует!",
        )

    db_new_category = Category(
        title=new_category.title,
    )

    session.add(db_new_category)
    await session.commit()
    await session.refresh(db_new_category)

    return db_new_category
