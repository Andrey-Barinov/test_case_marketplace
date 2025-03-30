from datetime import datetime
from typing import Optional

from fastapi import Form
from pydantic import BaseModel, ConfigDict, HttpUrl


class ArticleCreate(BaseModel):
    title: str
    content: str
    category_id: int

    @classmethod
    def as_form(
        cls,
        title: str = Form(...),
        content: str = Form(...),
        category_id: int = Form(...),
    ):
        return cls(title=title, content=content, category_id=category_id)


class ArticleResponse(ArticleCreate):
    id: int
    image_url: Optional[HttpUrl]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
