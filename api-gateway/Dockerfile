cat > api-gateway/Dockerfile <<'DOCKER'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY wsgi.py .

# Frontend build (precisa existir a pasta api-gateway/frontend-dist no repo)
COPY frontend-dist ./frontend/dist

ENV PORT=5000
EXPOSE 5000

CMD ["sh", "-c", "gunicorn wsgi:app -b 0.0.0.0:${PORT} -w 2 --threads 4 --timeout 120"]
DOCKER
