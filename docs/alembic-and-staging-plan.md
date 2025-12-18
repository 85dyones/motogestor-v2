# Plano técnico: Alembic e deploy de staging

## Objetivos
- Padronizar o Alembic em todos os serviços que usam Postgres (users, management, financial, teamcrm).
- Gerar migrações iniciais alinhadas aos models atuais de cada serviço.
- Disponibilizar um script único de deploy de staging que puxa as imagens `latest` (ou a tag configurada), sobe o `docker-compose.prod.yml` em modo staging e aplica `alembic upgrade head` antes de considerar o deploy ok.

## Estrutura de arquivos
- `users-service/alembic.ini` e `users-service/migrations/` (env + versões) — já existia, agora com versão inicial.
- `management-service/alembic.ini` e `management-service/migrations/` — novo skeleton + migração inicial.
- `financial-service/alembic.ini` e `financial-service/migrations/` — novo skeleton + migração inicial.
- `teamcrm-service/alembic.ini` e `teamcrm-service/migrations/` — novo skeleton + migração inicial.
- `deploy_staging.sh` na raiz do repositório — orquestra pull das imagens, subida do compose em projeto `motogestor-staging`, espera o Postgres ficar pronto e roda `alembic upgrade head` em cada serviço dependente de banco antes do rollout final.

## Conteúdo inicial dos arquivos Alembic
Cada serviço passa a ter:

- `alembic.ini`: aponta `script_location = migrations` e usa `sqlalchemy.url = env_db_url` para delegar a URL ao `DATABASE_URL` do ambiente.
- `migrations/env.py`: importa os models para expor `target_metadata`, lê `DATABASE_URL` da env ou usa o fallback de desenvolvimento do serviço e configura os modos offline/online.
- `migrations/README.md`: instruções rápidas de como gerar novas revisões (`alembic revision --autogenerate -m "msg"` e `alembic upgrade head`).
- `migrations/versions/*_initial_schema.py`: migração inicial já descrita com as tabelas atuais de cada serviço.

## Fluxo sugerido para novas migrações
1. Entrar na pasta do serviço (`cd users-service`, por exemplo).
2. Garantir que `DATABASE_URL` aponta para um banco com o estado atual.
3. Rodar `alembic revision --autogenerate -m "sua-mudanca"`.
4. Conferir/ajustar a revisão gerada em `migrations/versions`.
5. Aplicar com `alembic upgrade head` e commitar a revisão.

### Políticas de RLS e role de aplicação
- As migrações novas habilitam RLS por `tenant_id` (ou `id` no caso de `tenants`) usando a role `motogestor_app`.
- As políticas dependem do `current_setting('app.current_tenant')`; os serviços setam `SET LOCAL app.current_tenant = <tenant_id>` via middleware (`tenant_guard.inject_current_tenant_from_token`) quando o banco é Postgres.
- Para isolar por tenant em produção/staging, utilize uma connection string com usuário `motogestor_app` (ex.: `postgresql://motogestor_app:...@host/db`) ou `SET ROLE motogestor_app` após o pool conectar.

## Deploy de staging com migrações
- O script `./deploy_staging.sh` configura `APP_ENV=staging` e `COMPOSE_PROJECT_NAME=motogestor-staging`.
- Ele carrega variáveis de `.env`, faz `docker compose --env-file .env -f docker-compose.prod.yml pull` (imagens tag `latest` por padrão) e sobe `postgres`/`redis` primeiro.
- Aguarda o Postgres ficar saudável (`pg_isready` via `docker compose exec`), roda `alembic upgrade head` em `users-service`, `management-service`, `financial-service` e `teamcrm-service`, e só então sobe o restante dos serviços.
- Ao final, mostra `docker compose ps` para confirmar o estado dos contêineres.
