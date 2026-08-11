# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.12.2 /uv /uvx /bin/

# Install declared production dependencies before copying application source for
# efficient layer caching. A lockfile should be committed once dependencies exist.
COPY pyproject.toml README.md uv.lock ./
RUN uv sync --no-dev --no-install-project

COPY src ./src
RUN uv sync --no-dev

CMD ["python", "-c", "print('Project Atlas foundation image: no service is configured yet.')"]
