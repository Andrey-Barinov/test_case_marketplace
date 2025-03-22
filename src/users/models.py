import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from src.utils import pwd_context


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        default=uuid.uuid4, primary_key=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone_number: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    def set_password(self, password: str):
        """Хеширует пароль и сохраняет его в `password_hash`."""
        self.password_hash = pwd_context.hash(password)

    def check_password(self, password: str) -> bool:
        """Проверяет, соответствует ли введённый пароль хешу."""
        return pwd_context.verify(password, self.password_hash)

    def __repr__(self):
        return f"<User {self.user_id} - {self.email} - {self.phone_number}>"
