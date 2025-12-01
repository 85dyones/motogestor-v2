# financial-service/Dockerfile
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=5003

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} wsgi:app"]

# Test target: CI can build this target and run tests inside the container.
FROM runtime AS test
COPY tests ./tests
