# Deploy no Easypanel (Hostinger)

Este guia assume que você já criou o projeto no Easypanel e que o repositório foi clonado na VPS. Ele usa o `docker-compose.prod.yml` (otimizado com imagens do GHCR) para evitar problemas de build remoto.

## ⚠️ Importante: Qual arquivo Docker Compose usar?

- **`docker-compose.prod.yml`** ← **Use este arquivo no Easypanel**
  - Usa imagens pré-construídas do GHCR (recomendado para production e Easypanel).
  - Evita erros de build remoto e é mais rápido para deploy.
  - Não requer que os Dockerfiles estejam no servidor.

- **`docker-compose.yml`** (desenvolvimento)
  - Usa `build:` para construir imagens localmente.
  - Use apenas localmente na máquina de desenvolvimento.

- **`docker-compose.easypanel.yml`** (compatível, mantido para referência)
  - Equivalente ao `docker-compose.prod.yml`, usa imagens GHCR.
  - Pode ser usado alternativamente, mas `prod.yml` é a versão principal.

## Variáveis de ambiente
Crie um arquivo `.env` na raiz do repositório com pelo menos:

```
POSTGRES_USER=motogestor
POSTGRES_PASSWORD=troque-esta-senha
POSTGRES_DB=motogestor
JWT_SECRET_KEY=troque-esta-chave
LOG_LEVEL=INFO
```

O `docker-compose.prod.yml` já referencia o `.env` automaticamente. No Easypanel, você pode cadastrar as mesmas variáveis na interface de ambiente para sobrescrever valores sem editar o arquivo.

## Passos de deploy
1. Garanta que o Docker e o Docker Compose estão instalados na VPS (Easypanel já traz Docker).
2. Faça login no GHCR se as imagens forem privadas: `docker login ghcr.io -u <github-username> -p <token-com-read:packages>`.
3. Faça login no painel e crie um projeto que rode um comando customizado (via "Docker Compose App").
4. No campo de comando, use `IMAGE_TAG=0.0.1 docker compose -f docker-compose.prod.yml up -d`.
   - **Não use `--build`** (as imagens já estão construídas no GHCR).
   - Se a configuração do Easypanel não permitir remover `--build`, adicione um `.dockerignore` ou ignore o erro se apenas imagens forem puxadas.
5. Para aplicar migrations antes de subir os serviços, rode manualmente:
   ```
   docker compose -f docker-compose.prod.yml run --rm users-service flask db upgrade
   ```
   (Alembic/Flask-Migrate usa as mesmas variáveis do `.env`).
5. Exponha a porta 80 (já mapeada para o gateway) e configure HTTPS/LetsEncrypt pelo painel se necessário.

## Healthchecks
- Postgres: `pg_isready` garante que o banco está aceitando conexões antes de subir dependentes.
- users-service: `GET /health` checa conexão com Postgres e responde 200.
- api-gateway: `GET /health` confere dependência do users-service.

Easypanel interpreta healthchecks do Compose e reinicia containers que falharem, o que evita respostas inconsistentes.

## Observabilidade e logs
- Os serviços já configuram `LOG_LEVEL` e usam logging estruturado. No Easypanel, visualize logs pelo painel ou via `docker compose logs -f api-gateway`.
- Para tracing/correlação, utilize o cabeçalho `X-Request-ID` no gateway (ou configure um proxy reverso que o injete) e propague para os serviços conforme o middleware existente.

## Multi-tenant e segurança
- O gateway e o users-service esperam que o JWT contenha `tenant_id` e `plan`; tokens emitidos no login já incluem os campos.
- As rotas aplicam escopo de tenant nas queries; certifique-se de usar bancos e secrets diferentes por ambiente.

## Checklist pós-deploy
- [ ] `.env` com secrets fortes e senha de banco rotacionada.
- [ ] `docker compose -f docker-compose.prod.yml ps` mostra todos os serviços como `healthy`.
- [ ] Certificado HTTPS habilitado no domínio.
- [ ] Backups do volume `pgdata-prod` configurados pela VPS.

## Usando GitHub como fonte no Easypanel
Se preferir que o Easypanel faça o clone direto do GitHub (com atualizações contínuas), use o modo **Git** na criação do app:

1. Gere uma chave SSH no painel (botão “Gerar Chave SSH”) e cadastre-a como **Deploy Key** com acesso de leitura no repositório GitHub.
2. Preencha os campos do formulário Git conforme a captura acima:
   - **URL do Repositório**: `git@github.com:<sua-org>/motogestor-v2.git`
   - **Ramo**: `main` (ou outro branch de produção)
   - **Caminho de Build**: `/` (raiz do repo)
   - **Arquivo Docker Compose**: `docker-compose.prod.yml`
3. Confirme o app; o Easypanel fará o clone e executará `docker compose -f docker-compose.prod.yml up -d` usando seu `.env`.
4. Para atualizar, faça push no branch monitorado e use o botão de **Atualizar**/redeploy no painel. Se quiser automatizar, habilite webhooks do GitHub apontando para o endpoint de auto-deploy do Easypanel.

> Dica: mantenha o `.env` cadastrado no painel (não versionado) e habilite "Recriar containers" no redeploy para garantir que novas imagens sejam aplicadas.

## Testando o deploy localmente (pré-deployment)

Antes de fazer deploy no Easypanel, teste o `docker-compose.easypanel.yml` localmente com imagens do GHCR:

### Pré-requisitos
- Docker e Docker Compose instalados localmente.
- Acesso ao GHCR (login via `docker login ghcr.io` se as imagens forem privadas).
- Um arquivo `.env` com as variáveis necessárias.

### Passos

1. **Clonar o repositório e navegar até a raiz:**
   ```bash
   cd /caminho/para/motogestor-v2
   ```

2. **Criar um arquivo `.env.test` de teste (sem secrets reais):**
   ```bash
   cp .env.example .env.test  # se existir
   # ou crie manualmente:
   cat > .env.test << EOF
   POSTGRES_USER=motogestor_test
   POSTGRES_PASSWORD=senha-teste-local
   POSTGRES_DB=motogestor_test
   JWT_SECRET_KEY=chave-teste-nao-use-em-prod
   OPENAI_API_KEY=sk-test-fake
   DATABASE_URL=postgresql://motogestor_test:senha-teste-local@postgres:5432/motogestor_test
   LOG_LEVEL=DEBUG
   EOF
   ```

3. **Fazer login no GHCR (se necessário):**
   ```bash
   docker login ghcr.io
   # Entre com seu usuário do GitHub e um PAT (Personal Access Token) com escopo read:packages
   ```

4. **Validar a sintaxe do Compose:**
   ```bash
   docker compose -f docker-compose.easypanel.yml config --env-file .env.test
   ```

5. **Iniciar os containers em background:**
   ```bash
   docker compose -f docker-compose.easypanel.yml --env-file .env.test up -d
   ```

6. **Verificar o status dos containers:**
   ```bash
   docker compose -f docker-compose.easypanel.yml --env-file .env.test ps
   # Todos devem estar como "healthy" ou "running" após alguns segundos
   ```

7. **Testar endpoints principais:**
   ```bash
   # Health check do gateway
   curl http://localhost/health

   # Health check do users-service (acesso direto)
   docker compose -f docker-compose.easypanel.yml --env-file .env.test exec users-service \
     curl -s http://localhost:5000/health

   # Listar bancos de dados Postgres
   docker compose -f docker-compose.easypanel.yml --env-file .env.test exec postgres \
     psql -U motogestor_test -d motogestor_test -c "\dt"
   ```

8. **Verificar logs se houver erros:**
   ```bash
   # Logs de um serviço específico
   docker compose -f docker-compose.easypanel.yml --env-file .env.test logs -f api-gateway

   # Logs de todos os serviços
   docker compose -f docker-compose.easypanel.yml --env-file .env.test logs -f
   ```

9. **Parar e remover containers:**
   ```bash
   docker compose -f docker-compose.easypanel.yml --env-file .env.test down -v
   # A flag `-v` remove também os volumes (dados do banco)
   ```

### Validação e Checklist de Teste

- [ ] Todos os containers iniciam e ficam `healthy` dentro de 30s
- [ ] `curl http://localhost/health` retorna 200 OK
- [ ] Migrations do Postgres rodam sem erro
- [ ] Logs do gateway não mostram erros de conexão com serviços internos
- [ ] Variáveis de ambiente são aplicadas corretamente (verifique `docker inspect`)
- [ ] Volumes são criados e montados corretamente
- [ ] Rede entre containers funciona (ex: `docker exec <container> ping <outro-container>`)

### Troubleshooting Comum

**Erro: "image not found"**
- Verifique se as imagens `ghcr.io/85dyones/motogestor-v2-*:0.0.1` foram publicadas no GHCR.
- Execute `docker pull ghcr.io/85dyones/motogestor-v2-users:0.0.1` para testar acesso.

**Erro: "connection refused" entre serviços**
- Verifique se a rede do compose está correta: `docker network ls | grep motogestor`
- Confirme que `depends_on` está configurado no YAML.

**Banco de dados não inicializa**
- Verifique variáveis `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` no `.env.test`.
- Aumente o `retries` no healthcheck temporariamente para debug.

**Erro de permissão no GHCR**
- Confirme que seu PAT tem escopo `read:packages` (imagens privadas) ou `public_repo` (se público).
- Use `docker login ghcr.io` novamente se o token expirou.

## Fazendo deploy no Easypanel

Após testar localmente e confirmar que tudo funciona:

1. Entre no painel Easypanel/Hostinger.
2. Crie um novo "Docker Compose App" ou atualize um existente.
3. Cole o conteúdo de `docker-compose.easypanel.yml` ou aponte para a URL do repositório.
4. Configure as variáveis de ambiente conforme seção "[Variáveis de ambiente](#variáveis-de-ambiente)" acima.
5. Habilite "Recreate containers on redeploy" para garantir que novas imagens sejam puxadas.
6. Clique em "Deploy" ou "Atualizar".
7. Monitore os logs no painel por 2–5 minutos até que todos os serviços estejam saudáveis.
