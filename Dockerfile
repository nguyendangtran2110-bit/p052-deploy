# syntax=docker/dockerfile:1

FROM python:3.11.15-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -r requirements.txt


FROM python:3.11.15-slim-bookworm AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN groupadd --gid 1000 appuser \
    && useradd \
    --uid 1000 \
    --gid appuser \
    --system \
    --no-create-home \
    appuser \
    && mkdir -p /app/data \
    && chown appuser:appuser /app/data
# Copy Python packages đã cài từ builder sang stage-1

# Copy các file thực thi (như alembic, uvicorn, gunicorn, v.v.)

COPY --from=builder /opt/venv /opt/venv
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

HEALTHCHECK \
    --interval=30s \
    --timeout=3s \
    --start-period=10s \
    --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]

CMD ["sh", "-c", "alembic upgrade head && exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"]