FROM python:3.11-slim

# Project is Python 3.11 per .python-version
WORKDIR /app

# Install uv so we can honor uv.lock
COPY --from=ghcr.io/astral-sh/uv:0.5.23 /uv /bin/uv

# Install dependencies first (cached if pyproject.toml/lock unchanged)
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

# Application source
COPY backend/ backend/
COPY index.html app.js md.js ./

# docker-entrypoint ships the env check
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
