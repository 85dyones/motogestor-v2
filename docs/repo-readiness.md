# Repo readiness & next steps

## What is currently verified
- **Users-service unit/integration tests**: `pytest` passes locally (covers `/auth/login`, `/auth/me`, and `/users/seed-demo` flows with tenant-aware JWT handling).
- **Production Compose build paths**: `docker-compose.prod.yml` builds `users-service` and `api-gateway` from the repo root with explicit Dockerfiles, preventing missing-context errors on Easypanel.
- **Environment template**: `.env.example` lists required secrets for database, JWT, and logging levels used across compose files.

## Recommended next actions
1. **Run migrations in each environment**: execute `docker compose -f docker-compose.prod.yml run --rm users-service flask db upgrade` after provisioning Postgres, and add the same command to release automation.
2. **Add CI pipelines**: automate `pytest` in `users-service`, frontend lint/tests (if present), and a Compose build to catch regressions before deploy.
3. **Smoke tests after deploy**: script health checks for `api-gateway` and `users-service` (`/health`) plus a login + `/auth/me` round-trip against production URLs.
4. **Secrets & tenant hardening**: ensure unique `JWT_SECRET_KEY` per environment and consider rotating keys with downtime-aware rollout; keep per-tenant data scoping in place for any new queries.
5. **Frontend build verification**: run `npm install`/`npm run build` (or `pnpm` if preferred) to guarantee Vite bundles cleanly with current API shapes before promoting to production.
6. **Monitoring & backups**: configure Postgres volume backups (`pgdata-prod`) and aggregate structured logs from gateway/services; enable HTTPS/Let’s Encrypt on the gateway ingress.

## Quick checklist before the next deploy
- [ ] `.env` filled with strong secrets and DB credentials for the target environment.
- [ ] Database migrations applied and DB reachable by services.
- [ ] `docker compose -f docker-compose.prod.yml up -d --build` completes without context errors.
- [ ] `/health` endpoints return OK for gateway and users-service; login/me flows succeed.
- [ ] Frontend bundle built and served by the gateway (or CDN) with environment URLs configured.
