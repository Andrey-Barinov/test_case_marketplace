from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from .settings import test_settings

engine = create_async_engine(test_settings.TEST_DATABASE_URL, echo=True)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_test_async_session() -> AsyncSession:
    # Создаем новую сессию каждый раз
    new_session = async_session()
    try:
        yield new_session
    finally:
        await new_session.close()
