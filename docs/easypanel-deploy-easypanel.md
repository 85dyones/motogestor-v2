# Deploy no Easypanel (compose com imagens)

Este documento complementa `docs/easypanel-deploy.md` com um fluxo recomendado para o Easypanel usando imagens de container públicas (registry).

1. Build e push das imagens (exemplo GHCR):

```bash
# Login GHCR
echo $CR_PAT | docker login ghcr.io -u 85dyones --password-stdin
# Build e push
docker build -t ghcr.io/85dyones/motogestor-v2-users:latest users-service
docker push ghcr.io/85dyones/motogestor-v2-users:latest
# repetir para api-gateway, management-service, financial-service, teamcrm-service, ai-service
```

2. No repositório, há um arquivo `docker-compose.easypanel.yml` com placeholders `ghcr.io/...`. Substitua as tags por aquelas publicadas (ou use `:vX.Y.Z`).

3. No Easypanel crie uma nova stack usando o arquivo `docker-compose.easypanel.yml` e configure variáveis de ambiente / secrets na UI.

4. Se preferir DB gerenciado, não inclua `postgres` no compose e configure `DATABASE_URL` apontando para o DB externo.

5. SSL: configure domínio e certificados via Easypanel; a stack expõe `api-gateway` na porta 80 (compose). Configure redirecionamento 80→443 conforme o painel.

Observações de segurança
- Não commit IDs de tokens ou chaves no `.env` do repositório. Use os secrets do painel.
- Habilite backups do volume do Postgres no servidor Easypanel.

CI / validação automática

Há um workflow de CI no repositório (`.github/workflows/ci-build-and-test.yml`) que valida automaticamente os Dockerfiles construindo as imagens (sem fazer push) e executa testes quando presentes (por exemplo `users-service/tests`). Esse workflow roda em pull requests e em pushes para `main` — ele ajuda a prevenir regressões de build antes do merge.

