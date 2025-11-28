# api-gateway/app/config.py
import os

USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://users-service:5001")
MANAGEMENT_SERVICE_URL = os.getenv("MANAGEMENT_SERVICE_URL", "http://management-service:5002")
FINANCIAL_SERVICE_URL = os.getenv("FINANCIAL_SERVICE_URL", "http://financial-service:5003")
TEAMCRM_SERVICE_URL = os.getenv("TEAMCRM_SERVICE_URL", "http://teamcrm-service:5004")
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://ai-service:5005")

# Caminho onde o build do React (Vite) será copiado dentro do container
FRONTEND_DIST_PATH = os.getenv("FRONTEND_DIST_PATH", "/app/frontend/dist")
