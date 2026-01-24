# CLAUDE.md - MotoGestor v2 Codebase Guide for AI Assistants

> **Last Updated**: 2026-01-24
> **Purpose**: Comprehensive guide for AI assistants working with the MotoGestor v2 codebase

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Directory Structure](#directory-structure)
5. [Development Patterns](#development-patterns)
6. [Multi-Tenant System](#multi-tenant-system)
7. [Authentication & Authorization](#authentication--authorization)
8. [Database & Migrations](#database--migrations)
9. [API Gateway](#api-gateway)
10. [Observability](#observability)
11. [Testing Strategy](#testing-strategy)
12. [Docker & Deployment](#docker--deployment)
13. [CI/CD Pipeline](#cicd-pipeline)
14. [Key Conventions for AI Assistants](#key-conventions-for-ai-assistants)
15. [Common Tasks](#common-tasks)
16. [Troubleshooting](#troubleshooting)

---

## Project Overview

**MotoGestor v2** is a multi-tenant SaaS platform for motorcycle workshop management. The system provides:
- Workshop operations management (service orders, inventory, customer management)
- Financial management (receivables, payables, cash flow)
- Team/CRM capabilities
- AI-powered features (automated quotes, suggestions)
- n8n automation integration (`https://n8n.v2o5.com.br`)

### Business Model
- **Multi-tenant**: Each workshop (tenant) has isolated data
- **Plan-based**: BASIC, PREMIUM plans with feature gating
- **Omnichannel**: WhatsApp/Telegram integration for customer communication

---

## Architecture

### Microservices Architecture
```
┌─────────────┐
│  Frontend   │ (React + Vite + TailwindCSS)
└──────┬──────┘
       │
┌──────▼──────────────────────────────────────────┐
│           API Gateway (Flask)                    │
│  - Authentication enforcement                    │
│  - Request forwarding & tenant propagation       │
│  - Serves frontend static files                  │
└──────┬──────────────────────────────────────────┘
       │
       ├─────────┬─────────┬──────────┬──────────┬──────────┐
       │         │         │          │          │          │
┌──────▼────┐ ┌─▼─────┐ ┌─▼──────┐ ┌─▼──────┐ ┌─▼─────┐ ┌─▼────┐
│  Users    │ │ Mgmt  │ │Financial│ │Team/CRM│ │  AI   │ │ n8n  │
│  Service  │ │Service│ │ Service │ │Service │ │Service│ │(ext) │
└───────────┘ └───────┘ └─────────┘ └────────┘ └───────┘ └──────┘
       │         │           │           │          │
       └─────────┴───────────┴───────────┴──────────┘
                          │
                    ┌─────▼─────┐      ┌───────┐
                    │ PostgreSQL│      │ Redis │
                    └───────────┘      └───────┘
```

### Services Breakdown

| Service | Port | Responsibility | Database |
|---------|------|----------------|----------|
| **users-service** | 5000/5001 | Authentication, user management, tenant management | PostgreSQL |
| **management-service** | 5002 | Service orders, inventory, customers, vehicles | PostgreSQL |
| **financial-service** | 5003 | Receivables, payables, cash flow | PostgreSQL |
| **teamcrm-service** | 5004 | Team collaboration, CRM features | PostgreSQL |
| **ai-service** | 5005 | OpenAI integration, automated quotes | None (stateless) |
| **api-gateway** | 5000 (prod: 80) | Request routing, auth enforcement, frontend serving | None |

---

## Tech Stack

### Backend (All Services)
- **Language**: Python 3.11+
- **Framework**: Flask 3.0.3
- **WSGI Server**: Gunicorn 21.2.0
- **ORM**: SQLAlchemy 3.1.1 via Flask-SQLAlchemy
- **Database Driver**: psycopg2-binary 2.9.9
- **Migrations**: Alembic 1.13.2
- **Authentication**: flask-jwt-extended 4.6.0
- **Validation**: Pydantic 2.7.4
- **Password Hashing**: passlib[bcrypt] 1.7.4
- **Testing**: pytest 8.2.2, factory_boy 3.3.0, Faker 25.8.0

### Observability Stack
- **Metrics**: prometheus-flask-exporter 0.23.0, prometheus-client 0.20.0
- **Tracing**: OpenTelemetry SDK 1.25.0, OTLP exporter
- **Logging**: Structured JSON logs with trace_id and tenant_id

### Frontend
- **Framework**: React 18.3.1
- **Build Tool**: Vite 6.0.1
- **Router**: react-router-dom 6.28.0
- **Styling**: TailwindCSS 3.4.13
- **Icons**: lucide-react 0.474.0
- **Language**: TypeScript 5.6.3

### Infrastructure
- **Database**: PostgreSQL 17
- **Cache/Queue**: Redis 7
- **Orchestration**: Docker Compose
- **Container Registry**: GitHub Container Registry (GHCR)
- **Deployment**: Easypanel on Hostinger VPS

---

## Directory Structure

```
motogestor-v2/
├── users-service/              # User & tenant management
│   ├── app/
│   │   ├── __init__.py         # Flask app factory
│   │   ├── config.py           # Configuration management
│   │   ├── models.py           # SQLAlchemy models (User, Tenant, RevokedToken)
│   │   ├── routes_auth.py      # /auth endpoints (login, refresh, revoke)
│   │   ├── routes_users.py     # /users CRUD endpoints
│   │   ├── routes_seed.py      # /users/seed-demo for testing
│   │   ├── tenant_guard.py     # Multi-tenant enforcement decorators
│   │   ├── observability.py    # Logging, metrics, tracing setup
│   │   ├── errors.py           # Error handlers
│   │   └── schemas/            # Pydantic validation schemas
│   ├── migrations/             # Alembic migrations
│   │   └── versions/           # Migration scripts
│   ├── tests/                  # Unit & integration tests
│   ├── Dockerfile              # Multi-stage Docker build
│   ├── requirements.txt        # Python dependencies
│   ├── pytest.ini              # Pytest configuration
│   ├── alembic.ini             # Alembic configuration
│   └── wsgi.py                 # Gunicorn entry point
│
├── management-service/         # Workshop operations (similar structure)
│   ├── app/
│   │   ├── routes_customers.py
│   │   ├── routes_vehicles.py
│   │   ├── routes_service_orders.py
│   │   └── routes_inventory.py
│   └── ...
│
├── financial-service/          # Financial operations
│   ├── app/
│   │   ├── routes_receivables.py
│   │   ├── routes_payables.py
│   │   ├── routes_cashflow.py
│   │   └── tenant_guard.py     # Shared tenant enforcement pattern
│   └── ...
│
├── teamcrm-service/            # Team & CRM features
├── ai-service/                 # AI features (OpenAI integration)
│   ├── app/
│   │   ├── routes_ai.py        # AI endpoints
│   │   └── utils.py            # OpenAI helpers
│   └── ...
│
├── api-gateway/                # API Gateway & frontend serving
│   ├── app/
│   │   ├── __init__.py         # Gateway Flask app
│   │   ├── proxy.py            # Request forwarding utilities
│   │   ├── routes_services.py  # Proxy routes to services
│   │   ├── routes_auth.py      # Passthrough auth routes
│   │   └── identity.py         # JWT verification middleware
│   ├── Dockerfile              # Includes frontend/dist copy
│   └── ...
│
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── App.tsx             # Main app component
│   │   ├── pages/              # Page components
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── LoginPage.tsx
│   │   │   └── ...
│   │   ├── components/         # Reusable components
│   │   │   ├── layout/         # AppShell, Sidebar, Topbar
│   │   │   └── ui/             # Button, Card, Input, Badge
│   │   ├── contexts/           # React contexts
│   │   │   ├── AuthContext.tsx # Authentication state
│   │   │   └── ThemeContext.tsx
│   │   ├── lib/                # Utilities
│   │   │   └── api.ts          # API client
│   │   └── styles/             # Global styles
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── tests/                      # Cross-service tests
│   ├── contracts/              # Contract tests (service boundaries)
│   ├── e2e/                    # End-to-end tests
│   ├── requirements.txt
│   ├── start_stack.sh          # Helper to start services for testing
│   └── run_e2e.sh
│
├── docs/                       # Documentation
│   ├── architecture-improvement-plan.md  # Roadmap & evolution
│   ├── easypanel-deploy.md     # Production deployment guide
│   ├── observability.md        # Logging, metrics, tracing guide
│   └── alembic-and-staging-plan.md
│
├── .github/workflows/          # CI/CD pipelines
│   ├── ci-build-and-test.yml   # Build, test, publish images
│   ├── build-and-push-images.yml
│   └── migration-check.yml
│
├── docker-compose.yml          # Production compose (GHCR images)
├── docker-compose.dev.yml      # Development compose (local builds)
├── docker-compose.test.yml     # Test environment
├── docker-compose.observability.yml  # Prometheus + Grafana
├── .env.example                # Environment variables template
├── deploy_staging.sh           # Staging deployment script
└── README.md                   # Project readme
```

---

## Development Patterns

### 1. Flask App Factory Pattern
Every service uses the same structure in `app/__init__.py`:

```python
from flask import Flask
from flask_jwt_extended import JWTManager
from .config import load_config
from .models import db
from .observability import register_observability

def create_app() -> Flask:
    cfg = load_config()
    app = Flask(__name__)

    # Observability first
    register_observability(app, "service-name")

    # Configuration
    app.config["JWT_SECRET_KEY"] = cfg.jwt_secret_key
    app.config["SQLALCHEMY_DATABASE_URI"] = cfg.database_url

    # Extensions
    db.init_app(app)
    jwt = JWTManager(app)

    # Blueprints
    from .routes_something import bp
    app.register_blueprint(bp, url_prefix="/something")

    # Health endpoint
    @app.route("/health")
    def health():
        try:
            db.session.execute(text("SELECT 1"))
            return {"status": "ok", "service": "service-name"}, 200
        except OperationalError:
            return {"status": "degraded"}, 503

    return app
```

### 2. Configuration Management
Each service has `app/config.py`:

```python
from dataclasses import dataclass
import os

@dataclass
class Config:
    app_env: str
    database_url: str
    jwt_secret_key: str
    log_level: str

def load_config() -> Config:
    return Config(
        app_env=os.getenv("APP_ENV", "development"),
        database_url=os.getenv("DATABASE_URL", "postgresql://..."),
        jwt_secret_key=os.getenv("JWT_SECRET_KEY"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
```

### 3. Blueprint Structure
Routes are organized by resource in separate files:

```python
# app/routes_customers.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from .tenant_guard import tenant_guard
from .models import db, Customer

bp = Blueprint("customers", __name__)

@bp.route("/<int:tenant_id>/customers", methods=["GET"])
@jwt_required()
@tenant_guard()
def list_customers(tenant_id: int):
    # tenant_id is enforced by tenant_guard
    customers = Customer.query.filter_by(tenant_id=tenant_id).all()
    return jsonify([c.to_dict() for c in customers])
```

### 4. SQLAlchemy Models
Standard pattern with tenant_id foreign key:

```python
from .models import db

class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255))
    phone = db.Column(db.String(50))

    # Relationships
    tenant = db.relationship("Tenant", backref="customers")

    def to_dict(self):
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
        }
```

---

## Multi-Tenant System

### Tenant Isolation Strategy

**Level**: Row-Level Security (RLS) + Application-Level Guards

1. **Database Level**:
   - Every table (except `tenants` and `users`) has `tenant_id` column
   - PostgreSQL session variable: `SET LOCAL app.current_tenant = :tenant_id`
   - RLS policies can be applied for hard isolation (see financial-service migrations)

2. **Application Level**:
   - JWT contains `tenant_id` and `plan` claims
   - `tenant_guard` decorator enforces tenant matching on every request
   - Automatic query scoping via `g.current_tenant_id`

### Tenant Guard Implementation

Located in each service's `app/tenant_guard.py`:

```python
from functools import wraps
from flask import g, jsonify, request
from flask_jwt_extended import get_jwt, verify_jwt_in_request

def tenant_guard(path_key: str = "tenant_id", body_keys=("tenant_id",)):
    """
    Enforces tenant isolation by:
    1. Extracting tenant_id from JWT claims
    2. Extracting tenant_id from request (path or body)
    3. Ensuring they match
    4. Setting PostgreSQL session variable for RLS
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt() or {}
            token_tenant = claims.get("tenant_id")

            if token_tenant is None:
                return jsonify({"error": "token sem tenant"}), 403

            request_tenant = _extract_request_tenant(path_key, body_keys)
            if request_tenant is None:
                return jsonify({"error": "tenant_id obrigatório"}), 400

            if int(token_tenant) != int(request_tenant):
                return jsonify({"error": "tenant_id não corresponde"}), 403

            # Set context
            g.current_tenant_id = int(token_tenant)
            _set_pg_tenant_scope(int(token_tenant))

            return fn(*args, **kwargs)
        return wrapper
    return decorator
```

### Usage in Routes

```python
@bp.route("/<int:tenant_id>/service-orders", methods=["POST"])
@jwt_required()
@tenant_guard()  # Enforces tenant_id from path matches JWT
def create_service_order(tenant_id: int):
    data = request.get_json()
    # tenant_id is guaranteed to be correct here
    order = ServiceOrder(tenant_id=tenant_id, **data)
    db.session.add(order)
    db.session.commit()
    return jsonify(order.to_dict()), 201
```

### Plan-Based Feature Gating

JWT includes `plan` claim (BASIC, PREMIUM):

```python
from flask_jwt_extended import get_jwt

@bp.route("/<int:tenant_id>/ai/quote", methods=["POST"])
@jwt_required()
@tenant_guard()
def generate_ai_quote(tenant_id: int):
    claims = get_jwt()
    plan = claims.get("plan", "BASIC")

    if plan not in ["PREMIUM", "ENTERPRISE"]:
        return jsonify({"error": "AI features require PREMIUM plan"}), 403

    # Proceed with AI quote generation
    ...
```

---

## Authentication & Authorization

### JWT Structure

**Access Token** (short-lived, 1-2 hours):
```json
{
  "sub": 42,              // user_id
  "tenant_id": 10,        // tenant_id
  "plan": "PREMIUM",      // tenant plan
  "role": "OWNER",        // user role
  "jti": "uuid-...",      // unique token ID
  "exp": 1234567890,      // expiration
  "type": "access"
}
```

**Refresh Token** (longer-lived, 7-30 days):
```json
{
  "sub": 42,
  "tenant_id": 10,
  "jti": "uuid-...",
  "exp": 1234567890,
  "type": "refresh"
}
```

### Authentication Flow

1. **Login** (`POST /auth/login`):
   ```python
   # users-service/app/routes_auth.py
   @bp.route("/login", methods=["POST"])
   def login():
       data = request.get_json()
       user = User.query.filter_by(email=data["email"]).first()

       if not user or not check_password(data["password"], user.password_hash):
           return jsonify({"error": "invalid credentials"}), 401

       # Create tokens with tenant context
       access_token = create_access_token(
           identity=user.id,
           additional_claims={
               "tenant_id": user.tenant_id,
               "plan": user.plan,
               "role": user.role,
           }
       )
       refresh_token = create_refresh_token(
           identity=user.id,
           additional_claims={"tenant_id": user.tenant_id}
       )

       return jsonify({
           "access_token": access_token,
           "refresh_token": refresh_token,
           "user": user.to_dict()
       })
   ```

2. **Token Refresh** (`POST /auth/refresh`):
   ```python
   @bp.route("/refresh", methods=["POST"])
   @jwt_required(refresh=True)
   def refresh():
       current_user_id = get_jwt_identity()
       user = User.query.get(current_user_id)

       new_access_token = create_access_token(
           identity=user.id,
           additional_claims={
               "tenant_id": user.tenant_id,
               "plan": user.plan,
               "role": user.role,
           }
       )

       return jsonify({"access_token": new_access_token})
   ```

3. **Token Revocation** (`POST /auth/revoke`):
   - Uses `revoked_tokens` table with `jti` (JWT ID)
   - Checked on every request via `@jwt.token_in_blocklist_loader`

### API Gateway Auth Enforcement

The gateway enforces authentication before forwarding:

```python
# api-gateway/app/routes_services.py
from .identity import require_auth

@bp.route("/management/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE"])
@require_auth()  # Verifies JWT before forwarding
def proxy_management(subpath: str):
    return forward_request(MANAGEMENT_SERVICE_URL, subpath)
```

---

## Database & Migrations

### Database Schema Organization

**Shared Database**: All services share a single PostgreSQL database (`motogestor_prod`) but use different table namespaces and tenant isolation.

**Tenant Hierarchy**:
```
tenants (id, name, plan)
  └── users (id, tenant_id, email, password_hash, role, plan)
  └── customers (id, tenant_id, name, email, phone)
  └── vehicles (id, tenant_id, customer_id, plate, model, year)
  └── service_orders (id, tenant_id, vehicle_id, status, total)
  └── receivables (id, tenant_id, customer_id, amount, due_date, status)
  └── payables (id, tenant_id, supplier_id, amount, due_date, status)
  └── ...
```

### Alembic Migrations

Each service manages its own migrations in `migrations/versions/`:

```python
# financial-service/migrations/versions/20240904120002_initial_schema.py
"""initial schema

Revision ID: 20240904120002
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'receivables',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_receivables_tenant_id', 'receivables', ['tenant_id'])

def downgrade():
    op.drop_table('receivables')
```

### Running Migrations

**Development** (auto-run on container start if `APP_ENV=development`):
```bash
docker compose -f docker-compose.dev.yml up
```

**Production** (manual before deploy):
```bash
# Run migrations for each service
docker compose -f docker-compose.prod.yml run --rm users-service \
  alembic upgrade head

docker compose -f docker-compose.prod.yml run --rm financial-service \
  alembic upgrade head
```

### Creating New Migrations

```bash
# Enter service container
docker compose exec users-service bash

# Create migration
alembic revision -m "add_user_preferences_table"

# Edit the generated file in migrations/versions/
# Then apply
alembic upgrade head
```

---

## API Gateway

### Request Flow

```
Client Request
    ↓
API Gateway (:5000)
    ↓
1. Verify JWT (if protected route)
2. Extract tenant_id, plan from JWT
3. Add X-Tenant-ID, X-Plan headers
4. Forward to target service
    ↓
Target Service (:5001-5005)
    ↓
1. Re-verify JWT (optional, for defense in depth)
2. Extract tenant context
3. Apply tenant_guard
4. Execute business logic
    ↓
Response to API Gateway
    ↓
Response to Client
```

### Proxy Implementation

Located in `api-gateway/app/proxy.py`:

```python
def forward_request(base_url: str, subpath: str = "") -> Response:
    """
    Forwards the current request to a backend service.
    - Filters hop-by-hop headers
    - Preserves authentication headers
    - Passes query params, body, cookies
    """
    method = request.method
    url = base_url.rstrip("/") + "/" + subpath.lstrip("/")

    headers = _filter_request_headers()  # Removes Host, Connection, etc.

    resp = requests.request(
        method=method,
        url=url,
        headers=headers,
        params=request.args,
        data=request.get_data(),
        cookies=request.cookies,
        timeout=30,
    )

    return Response(resp.content, status=resp.status_code, headers=...)
```

### Service Routing

```python
# api-gateway/app/routes_services.py
USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://users-service:5000")
MANAGEMENT_SERVICE_URL = os.getenv("MANAGEMENT_SERVICE_URL", "http://management-service:5000")

@bp.route("/users/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE"])
@require_auth()
def proxy_users(subpath: str):
    return forward_request(USERS_SERVICE_URL, f"/users/{subpath}")

@bp.route("/management/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE"])
@require_auth()
def proxy_management(subpath: str):
    return forward_request(MANAGEMENT_SERVICE_URL, subpath)
```

### Frontend Serving

The gateway serves the React frontend:

```python
# api-gateway/app/__init__.py
from flask import send_from_directory

FRONTEND_DIST_PATH = os.getenv("FRONTEND_DIST_PATH", "../frontend/dist")

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path and os.path.exists(os.path.join(FRONTEND_DIST_PATH, path)):
        return send_from_directory(FRONTEND_DIST_PATH, path)
    return send_from_directory(FRONTEND_DIST_PATH, "index.html")
```

---

## Observability

### Three Pillars Implementation

Based on `docs/observability.md`:

#### 1. Structured Logging

**Format**: JSON with trace correlation
```json
{
  "timestamp": "2024-09-10T12:00:00+0000",
  "level": "INFO",
  "service": "users-service",
  "message": "login succeeded",
  "trace_id": "2f5c...",
  "tenant_id": 42,
  "route": "/auth/login"
}
```

**Setup** (in `app/observability.py`):
```python
import logging
import json
from flask import g, request

def register_observability(app: Flask, service_name: str):
    # JSON logging
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '{"timestamp":"%(asctime)s","level":"%(levelname)s",'
        '"service":"' + service_name + '","message":"%(message)s"}'
    )
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    # Middleware for trace_id propagation
    @app.before_request
    def inject_trace_id():
        g.trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))

    @app.after_request
    def add_trace_header(response):
        response.headers["X-Trace-ID"] = g.trace_id
        return response
```

#### 2. Prometheus Metrics

**Exposed Endpoint**: `/metrics` on all services

**Custom Metrics**:
- `http_request_latency_seconds{service,method,route}`
- `http_requests_total{service,method,route,status}`
- `auth_errors_total{service}`
- `os_created_total{tenant_id}` (management-service)

**Setup**:
```python
from prometheus_flask_exporter import PrometheusMetrics

def register_observability(app, service_name):
    metrics = PrometheusMetrics(app)
    metrics.info("app_info", "Application info", version="1.0.0")
```

#### 3. OpenTelemetry Tracing

**Enabled when**: `OTEL_EXPORTER_OTLP_ENDPOINT` is set

**Setup**:
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

def register_observability(app, service_name):
    if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        provider = TracerProvider(resource=Resource.create({
            "service.name": service_name
        }))
        processor = BatchSpanProcessor(OTLPSpanExporter())
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

        FlaskInstrumentor().instrument_app(app)
        RequestsInstrumentor().instrument()
```

### Healthchecks

All services expose `/health`:

```python
@app.route("/health")
def health():
    try:
        # Deep health: check database connectivity
        db.session.execute(text("SELECT 1"))
        return {"status": "ok", "service": "users-service"}, 200
    except OperationalError:
        return {"status": "degraded", "service": "users-service"}, 503
```

Docker Compose healthchecks:
```yaml
healthcheck:
  test: ["CMD-SHELL", "python -c 'import urllib.request; urllib.request.urlopen(\"http://localhost:5000/health\")'"]
  interval: 15s
  timeout: 5s
  retries: 10
```

---

## Testing Strategy

### Test Pyramid

```
        ┌─────────────┐
        │     E2E     │  ← Full stack (gateway + services + DB)
        └─────────────┘
      ┌─────────────────┐
      │   Integration   │  ← Service + DB
      └─────────────────┘
    ┌───────────────────────┐
    │   Contract Tests      │  ← Gateway ↔ Service boundaries
    └───────────────────────┘
  ┌───────────────────────────┐
  │      Unit Tests           │  ← Pure functions, models
  └───────────────────────────┘
```

### 1. Unit Tests

Located in each service's `tests/` directory:

```python
# users-service/tests/test_models.py
import pytest
from app.models import User, Tenant

def test_user_creation():
    tenant = Tenant(name="Workshop A", plan="BASIC")
    user = User(
        tenant=tenant,
        name="John Doe",
        email="john@example.com",
        password_hash="hashed..."
    )
    assert user.tenant_id == tenant.id
    assert user.plan == "BASIC"
```

**Run**:
```bash
cd users-service
pytest tests/
```

### 2. Integration Tests

Test service + database interaction:

```python
# users-service/tests/integration/test_auth_flow.py
import pytest
from app import create_app
from app.models import db

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://test_db"

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

def test_login_flow(client):
    # Seed user
    response = client.post("/users/seed-demo")
    assert response.status_code == 200

    # Login
    response = client.post("/auth/login", json={
        "email": "demo@motogestor.com",
        "password": "demo123"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert "access_token" in data
```

### 3. Contract Tests

Test gateway ↔ service communication:

```python
# tests/contracts/test_gateway_to_users.py
import requests

def test_gateway_forwards_to_users_health():
    # Assumes gateway and users-service are running
    resp = requests.get("http://localhost:8080/users/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "users-service"
```

### 4. E2E Tests

Full user flow tests located in `tests/e2e/`:

```python
# tests/e2e/test_service_order_flow.py
def test_create_service_order_end_to_end():
    # 1. Login
    login_resp = requests.post("http://localhost:8080/auth/login", json={
        "email": "demo@motogestor.com",
        "password": "demo123"
    })
    token = login_resp.json()["access_token"]

    # 2. Create customer
    customer_resp = requests.post(
        "http://localhost:8080/management/1/customers",
        json={"name": "João Silva", "phone": "11999999999"},
        headers={"Authorization": f"Bearer {token}"}
    )
    customer_id = customer_resp.json()["id"]

    # 3. Create service order
    so_resp = requests.post(
        "http://localhost:8080/management/1/service-orders",
        json={
            "customer_id": customer_id,
            "description": "Troca de óleo",
            "status": "PENDING"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert so_resp.status_code == 201
```

### Running Tests

**Local (per service)**:
```bash
cd users-service
pytest tests/
```

**Docker (isolated)**:
```bash
docker compose -f docker-compose.test.yml run --rm users-service pytest -q
```

**E2E (requires stack running)**:
```bash
./tests/start_stack.sh  # Starts all services
pytest tests/e2e/
```

**CI (GitHub Actions)**: Automated on every PR
- See `.github/workflows/ci-build-and-test.yml`

---

## Docker & Deployment

### Docker Compose Files

| File | Purpose | Image Source |
|------|---------|--------------|
| `docker-compose.yml` | **Production** (Easypanel) | GHCR pre-built images |
| `docker-compose.dev.yml` | Local development | Local builds (`build:`) |
| `docker-compose.test.yml` | Test environment | Local builds (test target) |
| `docker-compose.observability.yml` | Prometheus + Grafana | Public images |

### Multi-Stage Dockerfile Pattern

Every service uses this pattern:

```dockerfile
# users-service/Dockerfile
FROM python:3.11-slim AS base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Test stage
FROM base AS test
COPY . .
RUN pip install pytest factory_boy faker
CMD ["pytest", "-q"]

# Production stage
FROM base AS production
COPY . .
EXPOSE 5000 5001
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app", "--workers", "4"]
```

### Environment Variables

See `.env.example` for full list. Key variables:

```bash
# Database
POSTGRES_USER=motogestor
POSTGRES_PASSWORD=strong-password
POSTGRES_DB=motogestor_prod
DATABASE_URL=postgresql://user:pass@postgres:5432/db

# Auth
JWT_SECRET_KEY=very-strong-random-key

# Services (for gateway)
USERS_SERVICE_URL=http://users-service:5000
MANAGEMENT_SERVICE_URL=http://management-service:5000
FINANCIAL_SERVICE_URL=http://financial-service:5000
TEAMCRM_SERVICE_URL=http://teamcrm-service:5000
AI_SERVICE_URL=http://ai-service:5000

# AI
OPENAI_API_KEY=sk-...

# Observability
LOG_LEVEL=INFO
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318/v1/traces
```

### Local Development

```bash
# Start all services
docker compose -f docker-compose.dev.yml up --build

# Watch logs
docker compose -f docker-compose.dev.yml logs -f api-gateway

# Access
# Frontend: http://localhost
# API Gateway: http://localhost:5000
# Users Service: http://localhost:5001
# Management Service: http://localhost:5002
```

### Production Deployment (Easypanel)

See `docs/easypanel-deploy.md` for detailed guide.

**Quick steps**:

1. **Login to GHCR** (if images are private):
   ```bash
   docker login ghcr.io -u <github-username> -p <PAT-with-read:packages>
   ```

2. **Pull latest images**:
   ```bash
   IMAGE_TAG=0.0.1 docker compose -f docker-compose.prod.yml pull
   ```

3. **Run migrations**:
   ```bash
   docker compose -f docker-compose.prod.yml run --rm users-service alembic upgrade head
   docker compose -f docker-compose.prod.yml run --rm financial-service alembic upgrade head
   # ... for each service with migrations
   ```

4. **Start services**:
   ```bash
   IMAGE_TAG=0.0.1 docker compose -f docker-compose.prod.yml up -d
   ```

5. **Verify health**:
   ```bash
   docker compose -f docker-compose.prod.yml ps
   curl http://localhost/health
   ```

### Staging Deployment

Use `deploy_staging.sh`:

```bash
#!/bin/bash
export GHCR_USERNAME=your-github-username
export GHCR_TOKEN=your-pat-token
export IMAGE_TAG=staging

# Login, build, push, deploy
./deploy_staging.sh
```

---

## CI/CD Pipeline

### GitHub Actions Workflows

Located in `.github/workflows/`:

#### 1. CI - Build & Test (`ci-build-and-test.yml`)

**Triggers**: PR, push to tags

**Jobs**:
- **build-and-test** (matrix strategy):
  - Build each service image
  - Build test target
  - Run unit tests in workspace
  - Run tests inside Docker image

- **integration-tests**:
  - Spins up PostgreSQL
  - Runs integration tests for users-service

- **e2e-tests**:
  - Builds frontend
  - Builds all service images
  - Starts Postgres, Redis, all services
  - Runs E2E flow tests

- **publish** (only on tags):
  - Pushes images to GHCR
  - Tags: `latest`, `v1.2.3`, `1.2`, `sha-<commit>`

**Example tag trigger**:
```bash
git tag v0.0.2
git push origin v0.0.2
# Triggers full CI + publish to GHCR
```

#### 2. Migration Check (`migration-check.yml`)

Validates Alembic migrations on PR:
- Checks for conflicts
- Ensures migrations are idempotent
- Verifies downgrade scripts

### Image Versioning

Images are tagged as:
```
ghcr.io/85dyones/motogestor-v2-users:0.0.1
ghcr.io/85dyones/motogestor-v2-users:latest
ghcr.io/85dyones/motogestor-v2-users:sha-abc123
```

Update `docker-compose.yml` to reference new versions:
```yaml
services:
  users-service:
    image: ghcr.io/85dyones/motogestor-v2-users:0.0.2
```

---

## Key Conventions for AI Assistants

### Code Style

1. **Python**:
   - Use type hints where beneficial (function signatures)
   - Follow PEP 8 (enforced by future linting)
   - Use dataclasses for config/DTOs
   - Prefer explicit over implicit

2. **TypeScript/React**:
   - Functional components with hooks
   - Use TypeScript interfaces for props
   - Keep components small and focused
   - Use context for global state (AuthContext, ThemeContext)

3. **SQL/Migrations**:
   - Always include `tenant_id` foreign key for tenant-scoped tables
   - Add indexes on `tenant_id` for query performance
   - Use descriptive constraint names
   - Write both `upgrade()` and `downgrade()` functions

### Naming Conventions

- **Files**: `snake_case.py`, `PascalCase.tsx`
- **Routes**: `routes_<resource>.py` (e.g., `routes_customers.py`)
- **Blueprints**: Named after resource (e.g., `bp = Blueprint("customers", ...)`)
- **Models**: `PascalCase` (e.g., `Customer`, `ServiceOrder`)
- **Functions**: `snake_case` (e.g., `create_service_order()`)
- **React Components**: `PascalCase` (e.g., `DashboardPage`, `Button`)

### Multi-Tenant Checklist

When adding new features, ALWAYS:
- [ ] Add `tenant_id` to new tables
- [ ] Use `@tenant_guard()` decorator on routes
- [ ] Filter queries by `g.current_tenant_id`
- [ ] Include `tenant_id` in unique constraints where applicable
- [ ] Test with multiple tenants to verify isolation
- [ ] Consider plan-based feature gating if appropriate

### Security Checklist

- [ ] Never log passwords or tokens
- [ ] Always hash passwords with bcrypt via passlib
- [ ] Use parameterized queries (SQLAlchemy ORM does this)
- [ ] Validate input with Pydantic schemas
- [ ] Check authorization (tenant_guard) before business logic
- [ ] Use HTTPS in production (configured in Easypanel)
- [ ] Rotate JWT_SECRET_KEY between environments
- [ ] Set short `exp` on access tokens (1-2 hours)

### Testing Requirements

When adding features:
- [ ] Write unit tests for business logic
- [ ] Write integration test for DB operations
- [ ] Update contract tests if changing API surface
- [ ] Add E2E test for critical user flows
- [ ] Verify tests pass in CI before merging

### Documentation Requirements

When making significant changes:
- [ ] Update this CLAUDE.md if architecture changes
- [ ] Update relevant docs/ files
- [ ] Add inline comments for complex logic
- [ ] Update API route docstrings
- [ ] Update OpenAPI/Swagger if using (future enhancement)

---

## Common Tasks

### Adding a New Service

1. **Create service directory**:
   ```bash
   cp -r users-service new-service
   cd new-service
   ```

2. **Update `app/__init__.py`**:
   - Change service name in `register_observability(app, "new-service")`
   - Update routes

3. **Add to Docker Compose**:
   ```yaml
   # docker-compose.yml
   new-service:
     image: ghcr.io/85dyones/motogestor-v2-new:0.0.1
     environment:
       DATABASE_URL: ${DATABASE_URL}
       JWT_SECRET_KEY: ${JWT_SECRET_KEY}
     depends_on:
       postgres:
         condition: service_healthy
   ```

4. **Add gateway route**:
   ```python
   # api-gateway/app/routes_services.py
   NEW_SERVICE_URL = os.getenv("NEW_SERVICE_URL", "http://new-service:5000")

   @bp.route("/new/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE"])
   @require_auth()
   def proxy_new(subpath: str):
       return forward_request(NEW_SERVICE_URL, subpath)
   ```

5. **Add to CI/CD**:
   ```yaml
   # .github/workflows/ci-build-and-test.yml
   strategy:
     matrix:
       service:
         - name: new-service
           path: new-service
           has_tests: true
   ```

### Adding a Database Migration

```bash
# 1. Enter service container
docker compose exec users-service bash

# 2. Create migration
alembic revision -m "add_user_preferences_table"

# 3. Edit migration file
# migrations/versions/<timestamp>_add_user_preferences_table.py

def upgrade():
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('theme', sa.String(20), default='light'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_preferences_tenant_id', 'user_preferences', ['tenant_id'])

def downgrade():
    op.drop_table('user_preferences')

# 4. Apply migration
alembic upgrade head

# 5. Verify
psql $DATABASE_URL -c "\d user_preferences"
```

### Adding a New Frontend Page

```tsx
// 1. Create page component
// frontend/src/pages/CustomersPage.tsx
import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../lib/api';

export default function CustomersPage() {
  const { user } = useAuth();
  const [customers, setCustomers] = useState([]);

  useEffect(() => {
    if (user) {
      api.get(`/management/${user.tenant_id}/customers`)
        .then(res => setCustomers(res.data))
        .catch(err => console.error(err));
    }
  }, [user]);

  return (
    <div>
      <h1>Customers</h1>
      {customers.map(c => <div key={c.id}>{c.name}</div>)}
    </div>
  );
}

// 2. Add route
// frontend/src/App.tsx
import CustomersPage from './pages/CustomersPage';

<Route path="/customers" element={<CustomersPage />} />

// 3. Add to navigation
// frontend/src/components/layout/Sidebar.tsx
<NavLink to="/customers">Customers</NavLink>
```

### Adding a Protected API Route

```python
# management-service/app/routes_customers.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from .tenant_guard import tenant_guard
from .models import db, Customer

bp = Blueprint("customers", __name__)

@bp.route("/<int:tenant_id>/customers", methods=["POST"])
@jwt_required()  # Step 1: Verify JWT exists and is valid
@tenant_guard()  # Step 2: Verify tenant_id matches JWT claim
def create_customer(tenant_id: int):
    """
    Create a new customer.

    Request body:
    {
      "name": "João Silva",
      "email": "joao@example.com",
      "phone": "11999999999"
    }
    """
    data = request.get_json()

    # Validate (use Pydantic in production)
    if not data.get("name"):
        return jsonify({"error": "name is required"}), 400

    # Create
    customer = Customer(
        tenant_id=tenant_id,
        name=data["name"],
        email=data.get("email"),
        phone=data.get("phone")
    )

    db.session.add(customer)
    db.session.commit()

    return jsonify(customer.to_dict()), 201
```

### Debugging Issues

**Check service logs**:
```bash
docker compose logs -f users-service
```

**Check database**:
```bash
docker compose exec postgres psql -U motogestor -d motogestor_prod

\dt  -- List tables
\d users  -- Describe table
SELECT * FROM users WHERE tenant_id = 1;
```

**Check JWT token**:
```bash
# Decode JWT (paste token at jwt.io)
# Or use Python:
python3 -c "
import jwt
token = 'eyJ...'
print(jwt.decode(token, options={'verify_signature': False}))
"
```

**Test endpoints directly**:
```bash
# Login
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@motogestor.com", "password": "demo123"}'

# Use token
TOKEN="eyJ..."
curl http://localhost:5000/users/1/profile \
  -H "Authorization: Bearer $TOKEN"
```

---

## Troubleshooting

### Common Issues

#### 1. Service won't start - "connection refused to postgres"

**Cause**: Service starts before PostgreSQL is ready

**Solution**: Check healthcheck configuration in docker-compose.yml
```yaml
depends_on:
  postgres:
    condition: service_healthy  # Wait for healthcheck
```

#### 2. "403 tenant_id não corresponde"

**Cause**: JWT tenant_id doesn't match request tenant_id

**Debug**:
```python
# Print JWT claims
from flask_jwt_extended import get_jwt
print("JWT claims:", get_jwt())
print("Request tenant_id:", request.view_args.get("tenant_id"))
```

**Solution**: Ensure frontend sends correct tenant_id in API calls

#### 3. Migrations fail - "relation already exists"

**Cause**: Migration already applied or tables created manually

**Solution**:
```bash
# Mark migration as applied without running
alembic stamp head

# Or drop tables and re-run
alembic downgrade base
alembic upgrade head
```

#### 4. Frontend shows blank page

**Cause**: Build artifacts not copied to gateway

**Solution**:
```bash
# Rebuild frontend
cd frontend
npm run build

# Rebuild gateway (copies frontend/dist)
docker compose build api-gateway
docker compose up -d api-gateway
```

#### 5. GHCR image pull fails - "denied"

**Cause**: Not authenticated or PAT lacks permissions

**Solution**:
```bash
# Login with PAT that has read:packages scope
docker login ghcr.io -u <username> -p <PAT>

# Or make images public in GitHub repo settings
```

#### 6. High memory usage on dev machine

**Cause**: Too many services running

**Solution**:
```bash
# Run only essential services
docker compose -f docker-compose.dev.yml up postgres redis users-service api-gateway

# Or limit resources in docker-compose.yml
services:
  users-service:
    deploy:
      resources:
        limits:
          memory: 512M
```

#### 7. CORS errors in browser console

**Cause**: Frontend making requests to wrong origin

**Solution**: Ensure frontend uses gateway URL, not direct service URLs
```typescript
// frontend/src/lib/api.ts
const API_BASE = import.meta.env.VITE_API_URL || '';  // Empty string = same origin
export default axios.create({ baseURL: API_BASE });
```

---

## Additional Resources

### Internal Documentation
- `docs/architecture-improvement-plan.md` - Product roadmap and evolution plan
- `docs/easypanel-deploy.md` - Production deployment guide
- `docs/observability.md` - Logging, metrics, and tracing details
- `docs/alembic-and-staging-plan.md` - Migration strategy

### External Links
- **n8n Automation**: https://n8n.v2o5.com.br
- **Flask**: https://flask.palletsprojects.com/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **Alembic**: https://alembic.sqlalchemy.org/
- **React**: https://react.dev/
- **Vite**: https://vitejs.dev/
- **Docker Compose**: https://docs.docker.com/compose/

### Repository
- **GitHub**: https://github.com/85dyones/motogestor-v2
- **Issues**: https://github.com/85dyones/motogestor-v2/issues
- **GHCR**: https://github.com/85dyones?tab=packages

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-24 | Initial comprehensive CLAUDE.md created |

---

## Contact & Support

For questions about this codebase:
1. Check this CLAUDE.md file first
2. Review relevant docs/ files
3. Check GitHub issues
4. Review git commit history for context

**Remember**: This is a multi-tenant system. Always consider tenant isolation and plan-based feature gating when making changes.

---

**End of CLAUDE.md**
