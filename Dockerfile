FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app

COPY pyproject.toml README.md /app/
RUN pip install --upgrade pip && pip install poetry && poetry config virtualenvs.create false && poetry install --only main --no-interaction --no-ansi

COPY src /app/src
COPY alembic /app/alembic

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

