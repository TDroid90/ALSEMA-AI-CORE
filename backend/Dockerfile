FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml ./
RUN mkdir app && touch app/__init__.py && pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .
COPY app ./app
RUN pip install --no-cache-dir --no-deps .
FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN useradd --create-home --uid 10001 appuser
COPY --from=builder /usr/local /usr/local
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
