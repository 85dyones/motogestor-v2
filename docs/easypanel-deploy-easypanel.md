
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

Nota sobre testes em-container

Os Dockerfiles foram atualizados para incluir um stage `test` (target `test`) que copia a pasta `tests/` para dentro da imagem. O workflow de CI agora constrói esse target e executa os testes dentro da imagem para garantir que o ambiente interno da imagem também passa nos testes. Isso não altera a imagem final usada em produção (o target `test` é apenas um stage de build adicional).

Rodando testes de integração localmente

Se quiser rodar os testes de integração localmente (antes do CI):

1. Usando docker-compose (faz o serviço Postgres):
	 - inicie o compose (ou apenas o serviço Postgres):

		 docker compose up -d postgres

	 - exporte as variáveis de ambiente para apontar para o Postgres (exemplo):

		 export APP_ENV=development
		 export POSTGRES_USER=motogestor
		 export POSTGRES_PASSWORD=motogestor_pwd
		 export POSTGRES_HOST=localhost
		 export POSTGRES_DB=motogestor_integration

	 - rode os testes de integração do users-service:

		 python -m pytest users-service/tests/integration -q

2. Usando um container Postgres isolado:

		 docker run -d --name pg-test -e POSTGRES_USER=motogestor -e POSTGRES_PASSWORD=motogestor_pwd -e POSTGRES_DB=motogestor_integration -p 5432:5432 postgres:15

	 - e então rode os mesmos comandos de export e pytest do passo anterior.

