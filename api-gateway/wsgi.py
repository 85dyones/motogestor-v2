cat > api-gateway/wsgi.py <<'PY'
from app import create_app

app = create_app()
PY
