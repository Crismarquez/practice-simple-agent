FROM python:3.12-slim

WORKDIR /code

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (production only, no dev dependencies)
RUN uv sync --frozen --no-dev --no-editable

# Copy source code
COPY . .

EXPOSE 8080

CMD ["uv", "run", "gunicorn", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "debug", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8080", "--timeout", "120", "app.main:app"]
