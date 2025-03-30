import os

from fastapi import HTTPException, UploadFile

# Константы для валидации
ALLOWED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_IMAGE_SIZE_MB = 1
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024  # 1MB в байтах
MAX_TITLE_LENGTH = 200
MAX_CONTENT_LENGTH = 10000


class ImageValidator:
    @staticmethod
    async def validate_image(file: UploadFile) -> None:
        # Проверка расширения файла
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_IMAGE_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Неподдерживаемый формат изображения. Разрешены: "
                f"{', '.join(ALLOWED_IMAGE_FORMATS)}",
            )

        # Проверка размера файла
        content = await file.read()
        if len(content) > MAX_IMAGE_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"Размер файла превышает {MAX_IMAGE_SIZE_MB}MB",
            )

        # Сбрасываем позициsю файла в начало
        await file.seek(0)
