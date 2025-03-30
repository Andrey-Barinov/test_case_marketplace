import re
import uuid

import phonenumbers
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class UserRegisterSchema(BaseModel):
    email: EmailStr
    phone_number: str  # Просто строка, без constr
    name: str
    password: str
    password_confirm: str

    @field_validator("phone_number")
    def validate_phone(cls, value):
        # Убираем пробелы и приводим к стандартному формату
        value = value.strip().replace(" ", "")

        # Парсим номер
        try:
            parsed_number = phonenumbers.parse(value, "RU")
        except phonenumbers.NumberParseException:
            raise ValueError("Некорректный номер")

        # Проверяем его валидность
        if not phonenumbers.is_valid_number(parsed_number):
            raise ValueError("Номер невалиден")

        # Приводим к международному формату (+79998887766)
        return phonenumbers.format_number(
            parsed_number, phonenumbers.PhoneNumberFormat.E164
        )

    @field_validator("password")
    def validate_password(cls, value):
        """Проверка сложности пароля"""
        if not re.search(r"[A-Z]", value):
            raise ValueError(
                "Пароль должен содержать хотя бы одну заглавную букву"
            )
        if not re.search(r"[a-z]", value):
            raise ValueError(
                "Пароль должен содержать хотя бы одну строчную букву"
            )
        if not re.search(r"\d", value):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError("Пароль должен содержать хотя бы один спецсимвол")
        return value

    @field_validator("password_confirm")
    def passwords_match(cls, value, info):
        """Проверка совпадения паролей"""
        if "password" in info.data and value != info.data["password"]:
            raise ValueError("Пароли не совпадают")
        return value


class UserResponseSchema(BaseModel):
    user_id: uuid.UUID
    email: EmailStr
    phone_number: str
    name: str

    model_config = ConfigDict(from_attributes=True)
