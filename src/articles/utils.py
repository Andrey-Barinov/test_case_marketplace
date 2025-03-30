from uuid import uuid4

import aioboto3
from fastapi import UploadFile

from src.settings import settings

BUCKET_NAME = "articles"


# Функция загрузки изображения
async def upload_image_to_s3(file: UploadFile) -> str:
    file_name = f"{uuid4()}_{file.filename}"

    session = aioboto3.Session()
    async with session.client(
        "s3",
        endpoint_url=settings.MINIO_ENDPOINT,
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
    ) as s3_client:
        await s3_client.upload_fileobj(
            file.file, BUCKET_NAME, file_name, ExtraArgs={"ACL": "public-read"}
        )

    return f"{settings.MINIO_ENDPOINT}/{BUCKET_NAME}/{file_name}"


# Функция удаления изображения
async def delete_image_from_s3(file_path: str) -> None:
    file_name = file_path.split("/")[-1]

    session = aioboto3.Session()
    async with session.client(
        "s3",
        endpoint_url=settings.MINIO_ENDPOINT,
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
    ) as s3_client:
        await s3_client.delete_object(Bucket=BUCKET_NAME, Key=file_name)
