
# Deploy no Easypanel (compose com imagens ou build local)

Este documento complementa `docs/easypanel-deploy.md` com dois fluxos recomendados para o Easypanel:

- Usar imagens publicadas em um registry (ex: ghcr.io) — o host precisa estar autenticado se as imagens forem privadas.
- Fazer o Easypanel construir as imagens localmente a partir dos Dockerfiles do repositório (modo `build:` no Compose), útil quando você não deseja publicar imagens em um registry.

1. Build e push das imagens (exemplo GHCR):

```bash
# Geração do token (GHCR) — no GitHub, vá em Settings → Developer settings → Personal access tokens
# Crie um token com scope `read:packages` para pull (e `write:packages` para push se necessário).
# No host Easypanel (ou na máquina que fará o push):
echo $CR_PAT | docker login ghcr.io -u 85dyones --password-stdin

# Build e push (exemplo para o serviço de users):
docker build -t ghcr.io/85dyones/motogestor-v2-users:latest users-service
docker push ghcr.io/85dyones/motogestor-v2-users:latest

# Repita para api-gateway, management-service, financial-service, teamcrm-service, ai-service
#
# Observação (imagens privadas vs build local):

- Se você usar imagens no GHCR e elas forem privadas, o host Easypanel (ou as configurações de registry do painel) precisa estar autenticado para fazer pull.
- Se preferir não publicar imagens, configurar `build:` no `docker-compose.easypanel.yml` fará com que o host construa as imagens localmente a partir dos Dockerfiles. Isso é especialmente útil quando você cria a stack diretamente a partir do código do repositório no Easypanel.

Exemplo de comando (modo build — construindo localmente no host):

```bash
# estando no diretório do projeto no host Easypanel (ou dentro do workspace que contém o compose):
docker compose -f docker-compose.easypanel.yml up --build -d
```

Observações sobre o modo `build:` no Easypanel:
- O host precisa ter acesso ao código fonte (geralmente o painel clona o repositório antes de executar o compose).
- Construções podem demorar dependendo do tamanho do projeto e dos recursos do host — ajuste limites de CPU/RAM no Easypanel se necessário.
- Se preferir controle maior sobre versão das imagens, considere usar tags e publicar em um registry público/privado (GHCR/others) e usar `image:` em vez de `build:`.
```

2. No repositório, há um arquivo `docker-compose.easypanel.yml` com placeholders `ghcr.io/...`. Substitua as tags por aquelas publicadas (ou use `:vX.Y.Z`).

3. No Easypanel crie uma nova stack usando o arquivo `docker-compose.easypanel.yml` e configure variáveis de ambiente / secrets na UI.

4. Se preferir DB gerenciado, não inclua `postgres` no compose e configure `DATABASE_URL` apontando para o DB externo.

5. SSL: configure domínio e certificados via Easypanel; a stack expõe `api-gateway` na porta 80 (compose). Configure redirecionamento 80→443 conforme o painel.

Observações de segurança
- Não commit IDs de tokens ou chaves no `.env` do repositório. Use os secrets do painel.
- Habilite backups do volume do Postgres no servidor Easypanel.

