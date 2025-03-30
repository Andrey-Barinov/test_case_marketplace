"""Add full-text search index to articles

Revision ID: 5b174e843813
Revises: 94841b2dadbf
Create Date: 2025-03-24 17:07:11.258800

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b174e843813'
down_revision: Union[str, None] = '94841b2dadbf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Создаем индекс для полнотекстового поиска
    op.execute(
        """
        CREATE INDEX idx_articles_fts ON articles 
        USING gin(to_tsvector('russian', title || ' ' || content));
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Удаляем индекс при откате
    op.execute("DROP INDEX idx_articles_fts;")
