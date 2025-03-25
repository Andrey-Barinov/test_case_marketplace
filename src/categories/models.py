from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    articles: Mapped[list["Article"]] = relationship(  # noqa: F821
        "Article", back_populates="category"
    )
    deleted_articles: Mapped[list["DeletedArticle"]] = relationship(  # noqa: F821
        "DeletedArticle", back_populates="category"
    )
