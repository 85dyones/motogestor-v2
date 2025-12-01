FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY api-gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api-gateway/app ./app
COPY api-gateway/wsgi.py .

# build do frontend já deve existir em frontend/dist
COPY frontend/dist ./frontend/dist

ENV PORT=5000
EXPOSE 5000

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} wsgi:app"]

# Test target: optional stage for CI to include tests in the image (if they exist).
FROM runtime AS test
COPY tests ./tests
