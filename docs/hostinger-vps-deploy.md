# Deploy em VPS (Hostinger/Easypanel) com Compose

Estas instruções assumem que você já clonou o repositório na VPS. O objetivo é evitar erros de `Head "...": denied` ao puxar imagens do GHCR e garantir um caminho alternativo caso você prefira (ou precise) construir as imagens localmente.

## 1) Qual Compose usar?
- **Produção / Easypanel**: `docker-compose.prod.yml` (usa imagens do GHCR).  
  Defina `IMAGE_TAG` (padrão `latest`) e faça login no GHCR antes do `pull`.
- **Fallback sem GHCR**: `docker-compose.yml` (constrói localmente).  
  Use apenas se você não tiver acesso às imagens do GHCR.

> Se a VPS ainda tiver arquivos antigos (`docker-compose.easypanel*.yml`), remova-os e mantenha apenas `docker-compose.prod.yml` e `docker-compose.yml` para evitar referências inválidas como `*image_tag`.

## 2) Preparar secrets e login no GHCR
1. Crie um token do GitHub com escopo `read:packages`.
2. Faça login no GHCR:
   ```bash
   echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USERNAME" --password-stdin
   # ou rode: ./scripts/ghcr-login.sh .env
   ```
3. Valide o acesso à tag que será usada:
   ```bash
   IMAGE_TAG=latest
   ./scripts/check-ghcr-images.sh
   ```
   Se algum `pull` falhar com `denied`, revise o token/escopos ou deixe as imagens públicas.

## 3) Rodar com imagens do GHCR (recomendado)
1. Garanta um `.env` na raiz com as credenciais (veja `docs/easypanel-deploy.md`).
2. Suba apenas com imagens publicadas:
   ```bash
   IMAGE_TAG=latest docker compose -f docker-compose.prod.yml --env-file .env pull
   IMAGE_TAG=latest docker compose -f docker-compose.prod.yml --env-file .env up -d
   ```
3. Aplique migrations (se não usar o script `deploy_staging.sh`):
   ```bash
   IMAGE_TAG=latest docker compose -f docker-compose.prod.yml --env-file .env run --rm users-service alembic upgrade head
   IMAGE_TAG=latest docker compose -f docker-compose.prod.yml --env-file .env run --rm management-service alembic upgrade head
   IMAGE_TAG=latest docker compose -f docker-compose.prod.yml --env-file .env run --rm financial-service alembic upgrade head
   IMAGE_TAG=latest docker compose -f docker-compose.prod.yml --env-file .env run --rm teamcrm-service alembic upgrade head
   ```
4. Verifique health:
   ```bash
   docker compose -f docker-compose.prod.yml --env-file .env ps
   curl -f http://localhost/health
   ```

## 4) Fallback: construir localmente (sem GHCR)
Use este caminho apenas se você não puder puxar imagens do GHCR.

```bash
cp .env .env.local   # ou crie um .env com credenciais de teste
docker compose -f docker-compose.yml --env-file .env.local build
docker compose -f docker-compose.yml --env-file .env.local up -d

# migrations
docker compose -f docker-compose.yml --env-file .env.local run --rm users-service alembic upgrade head
docker compose -f docker-compose.yml --env-file .env.local run --rm management-service alembic upgrade head
docker compose -f docker-compose.yml --env-file .env.local run --rm financial-service alembic upgrade head
docker compose -f docker-compose.yml --env-file .env.local run --rm teamcrm-service alembic upgrade head
```

## 5) Dicas para o Easypanel
- Cadastre o token do GHCR em **Registries** e selecione-o no app para que o `pull` use credenciais válidas.
- Marque “Recreate containers on deploy” para forçar o uso da tag configurada.
- Confirme que o comando de deploy utiliza `docker-compose.prod.yml` e não inclui `--build`.
- Para trocar a tag, altere `IMAGE_TAG` no painel ou exporte no comando de deploy.

Seguindo estes passos, você terá um caminho suportado (puxando do GHCR) e um plano B (build local) para rodar o MotoGestor v2 na VPS ou no Easypanel.
