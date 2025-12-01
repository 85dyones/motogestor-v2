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

Publicação automática de imagens (opcional)

Além da validação, o mesmo workflow possui um job de publicação que *constrói e publica* as imagens no GitHub Container Registry (GHCR) quando você faz push para `main` ou criar uma tag do tipo `vX.Y.Z`.

Requisitos / permissões:
- O job usa o `GITHUB_TOKEN` para autenticação com o GHCR. Ele precisa de permissão `packages: write` (o workflow já configura isso) — ao usar o token padrão do Actions, garanta que o repositório e a organização permitam publicação com o `GITHUB_TOKEN`.
- Se preferir usar um PAT (personal access token) com escopo `write:packages`, configure-o em `Settings → Secrets` como `CR_PAT` e atualize o workflow para usá-lo.

Tags e versionamento:
- O workflow gera tags semânticas a partir de tags de release (ex: `v1.2.3`) e também marca `latest` quando for o branch padrão.

Se não quiser publicar automaticamente, você pode manter o workflow apenas para validação e manter a publicação manual ou controlada em outro workflow.

