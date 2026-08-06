"""Deterministic environment required while importing the application in unit tests."""

import os

os.environ.setdefault("APP_SECRET_KEY", "test-only-secret-key-that-is-long-enough")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("OLLAMA_BASE_URL", "http://localhost:11434")
