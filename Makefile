install:
	poetry install

db:
	docker run -p 5433:5432 --name marketplace_db -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=postgres -d postgres:17

clean:
	@echo "Removing test database container..."
	-docker stop marketplace_db
	-docker rm marketplace_db

migrate:
	poetry run python3 -m alembic upgrade head
dev:
	poetry run python3 -m uvicorn src.main:app --reload --port 8001

start:
	poetry run python3 -m gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app --bind=0.0.0.0:8000

lint_and_format:
	poetry run ruff check --fix


test:
	poetry run pytest -s -v
