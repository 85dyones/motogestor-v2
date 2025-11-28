# MotoGestor v2

SaaS para gestão de oficinas de motocicletas, baseado em microsserviços:

- Backend: Flask + Gunicorn
- Frontend: React + Vite
- Banco: PostgreSQL
- Cache/Filas: Redis
- Orquestração: Docker Compose
- Automação: n8n (`https://n8n.v2o5.com.br`)

Este repositório contém:
- Microsserviços (users, management, financial, team/CRM, AI)
- API Gateway
- Frontend
- Arquivos de infraestrutura (Docker, envs, docs).

## Deploy

Há um `docker-compose.yml` base para desenvolvimento local. Para produção (ex.: Easypanel/Hostinger), consulte [`docs/easypanel-deploy.md`](docs/easypanel-deploy.md) com passo a passo de `.env`, migrations e healthchecks usando o `docker-compose.prod.yml`.

Para uma visão de evolução e diferenciação do produto, veja o [`docs/architecture-improvement-plan.md`](docs/architecture-improvement-plan.md).
