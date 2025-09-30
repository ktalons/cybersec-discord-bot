# syntax=docker/dockerfile:1
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install minimal runtime dependencies
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user and workdir
RUN useradd -u 10001 -m appuser
WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY src ./src
COPY .env.example ./

# Drop privileges
USER appuser

# The bot reads configuration from environment variables
# Provide these via --env or --env-file when running the container
CMD ["python", "-m", "src.main"]
