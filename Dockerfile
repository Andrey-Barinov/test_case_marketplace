FROM docker.io/library/python:3.10

WORKDIR /app

RUN pip install poetry

COPY poetry.lock pyproject.toml ./

RUN poetry config virtualenvs.create false && poetry install --without dev

COPY . .

CMD ["sh", "-c", "poetry run python3 -m alembic upgrade head && poetry run python3 -m gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app --bind=0.0.0.0:8000"]
