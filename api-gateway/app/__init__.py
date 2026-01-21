# api-gateway/app/__init__.py
import os

import requests
from flask import Flask, current_app, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, get_jwt_identity, jwt_required

from .config import load_config
from .identity import extract_tenant_context
from .observability import register_observability
from .routes_auth import bp as auth_bp
from .routes_services import bp as services_bp


def create_app():
    service_name = "api-gateway"
    cfg = load_config()

    app = Flask(__name__)
    register_observability(app, service_name)

    # JWT (deve usar o MESMO segredo dos outros serviços)
    app.config["JWT_SECRET_KEY"] = cfg.jwt_secret_key
    app.config["ENV"] = cfg.app_env

    # CORS liberado pro frontend (ajusta depois se quiser fechar)
    CORS(app, supports_credentials=True)

    JWTManager(app)

    # ------------------------------------------------------------
    # ROTAS DE API
    #
    # Você já tinha /auth/* e /services/* (via blueprints).
    # Seu frontend chama /api/auth/*.
    # Então registramos os MESMOS blueprints em /api também.
    #
    # IMPORTANTE: blueprint não pode ser registrado 2x com o mesmo nome,
    # por isso usamos o parâmetro "name=".
    # ------------------------------------------------------------

    # rotas "legadas" (sem /api)
    app.register_blueprint(auth_bp)
    app.register_blueprint(services_bp)

    # rotas oficiais com /api
    app.register_blueprint(auth_bp, url_prefix="/api", name="auth_api")
    app.register_blueprint(services_bp, url_prefix="/api", name="services_api")

    # Health (mantém /health e cria /api/health)
    @app.route("/health", methods=["GET"])
    def health():
        return {"status": "ok", "service": "api-gateway"}, 200

    @app.route("/api/health", methods=["GET"])
    def api_health():
        return {"status": "ok", "service": "api-gateway"}, 200

    # ---------- Tema por tenant (BASIC / PRO / ENTERPRISE) ----------

    BASE_THEMES = {
        "BASIC": [
            {
                "id": "basic-blue",
                "name": "Oficina Azul",
                "primary": "#2563EB",
                "secondary": "#0EA5E9",
                "accent": "#F97316",
                "background": "#020617",
                "surface": "#0F172A",
            },
            {
                "id": "basic-dark",
                "name": "Garage Dark",
                "primary": "#F97316",
                "secondary": "#EAB308",
                "accent": "#22C55E",
                "background": "#020617",
                "surface": "#111827",
            },
        ],
        "PRO": [
            {
                "id": "pro-red",
                "name": "Racing Red",
                "primary": "#DC2626",
                "secondary": "#F97316",
                "accent": "#22C55E",
                "background": "#0B1120",
                "surface": "#111827",
            },
            {
                "id": "pro-green",
                "name": "Torque Green",
                "primary": "#16A34A",
                "secondary": "#22C55E",
                "accent": "#FBBF24",
                "background": "#022C22",
                "surface": "#064E3B",
            },
        ],
        "ENTERPRISE": [
            {
                "id": "enterprise-custom-base",
                "name": "Enterprise Custom Base",
                "primary": "#38BDF8",
                "secondary": "#6366F1",
                "accent": "#F97316",
                "background": "#020617",
                "surface": "#020617",
            }
        ],
    }

    def _tenant_theme_payload():
        """
        Retorna opções de paleta para o tenant atual, baseado no plano.
        Espera que o JWT contenha algo como:
        {
          "tenant_id": 1,
          "plan": "BASIC" | "PRO" | "ENTERPRISE",
          "tenant_name": "Oficina X"
        }
        """
        identity = extract_tenant_context(get_jwt_identity() or {})
        plan = identity.get("plan", "BASIC")
        tenant_name = identity.get("tenant_name")

        available_plans = ["BASIC", "PRO", "ENTERPRISE"]
        if plan not in available_plans:
            plan = "BASIC"

        themes_for_plan = BASE_THEMES.get(plan, BASE_THEMES["BASIC"])

        # Placeholder pra futuro: buscar palette custom do tenant em algum serviço
        custom_palette = None

        return {
            "tenant": {
                "id": identity.get("tenant_id"),
                "name": tenant_name,
                "plan": plan,
            },
            "themes": themes_for_plan,
            "custom_palette": custom_palette,
            "custom_allowed": plan in ("PRO", "ENTERPRISE"),
            "custom_only_enterprise": plan == "ENTERPRISE",
        }

    @app.route("/tenant/theme", methods=["GET"])
    @jwt_required()
    def tenant_theme():
        return jsonify(_tenant_theme_payload())

    @app.route("/api/tenant/theme", methods=["GET"])
    @jwt_required()
    def api_tenant_theme():
        return jsonify(_tenant_theme_payload())

    # ---------- Overview simples agregando serviços ----------

    def _overview_payload():
        auth_header = request.headers.get("Authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header

        summary = {}

        # OS (management-service)
        try:
            resp_os = requests.get(
                cfg.management_service_url.rstrip("/") + "/os",
                headers=headers,
                timeout=5,
            )
            if resp_os.ok:
                os_list = resp_os.json()
                open_status = {"OPEN", "IN_PROGRESS", "WAITING_PARTS"}
                summary["service_orders"] = {
                    "total": len(os_list),
                    "open": len([o for o in os_list if o.get("status") in open_status]),
                    "completed": len(
                        [o for o in os_list if o.get("status") == "COMPLETED"]
                    ),
                }
            else:
                summary["service_orders"] = {"error": resp_os.status_code}
        except Exception:
            summary["service_orders"] = {"error": "unavailable"}

        # Recebíveis pendentes (financial-service)
        try:
            resp_rec = requests.get(
                cfg.financial_service_url.rstrip("/") + "/receivables",
                headers=headers,
                params={"status": "PENDING"},
                timeout=5,
            )
            if resp_rec.ok:
                rec_list = resp_rec.json()
                summary["receivables"] = {
                    "pending_count": len(rec_list),
                    "pending_total": sum(float(r.get("amount", 0)) for r in rec_list),
                }
            else:
                summary["receivables"] = {"error": resp_rec.status_code}
        except Exception:
            summary["receivables"] = {"error": "unavailable"}

        # Tarefas abertas (teamcrm-service)
        try:
            resp_tasks = requests.get(
                cfg.teamcrm_service_url.rstrip("/") + "/tasks",
                headers=headers,
                params={"only_open": "1"},
                timeout=5,
            )
            if resp_tasks.ok:
                tasks = resp_tasks.json()
                summary["tasks"] = {"open_count": len(tasks)}
            else:
                summary["tasks"] = {"error": resp_tasks.status_code}
        except Exception:
            summary["tasks"] = {"error": "unavailable"}

        return summary

    @app.route("/overview", methods=["GET"])
    @jwt_required()
    def overview():
        return jsonify(_overview_payload())

    @app.route("/api/overview", methods=["GET"])
    @jwt_required()
    def api_overview():
        return jsonify(_overview_payload())

    # ---------- Frontend estático (React/Vite) ----------

    app.config["FRONTEND_DIST_PATH"] = cfg.frontend_dist_path

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path: str):
        """
        Serve arquivos estáticos do frontend.
        Se o arquivo não existir, devolve index.html (SPA).
        Se nem index existir, responde erro de frontend não construído.

        IMPORTANTE: /api/* não deve cair aqui (senão vira HTML e quebra tudo).
        """
        if path.startswith("api/"):
            return jsonify({"error": "api_route_not_found"}), 404

        dist_path = current_app.config["FRONTEND_DIST_PATH"]

        if path:
            file_path = os.path.join(dist_path, path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return send_from_directory(dist_path, path)

        index_path = os.path.join(dist_path, "index.html")
        if os.path.exists(index_path):
            return send_from_directory(dist_path, "index.html")

        return jsonify({"error": "frontend_not_built"}), 500

    return app
