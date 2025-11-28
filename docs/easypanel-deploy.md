# Deploy no Easypanel (Hostinger)

Este guia assume que você já criou o projeto no Easypanel e que o repositório foi clonado na VPS. Ele usa o `docker-compose.prod.yml` existente e foca na execução em modo production.

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
2. Faça login no painel e crie um projeto que rode um comando customizado (via "Docker Compose App").
3. No campo de comando, use `docker compose -f docker-compose.prod.yml up -d --build`.
4. Para aplicar migrations antes de subir os serviços, rode manualmente:
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
3. Confirme o app; o Easypanel fará o clone e executará `docker compose -f docker-compose.prod.yml up -d --build` usando seu `.env`.
4. Para atualizar, faça push no branch monitorado e use o botão de **Atualizar**/redeploy no painel. Se quiser automatizar, habilite webhooks do GitHub apontando para o endpoint de auto-deploy do Easypanel.

> Dica: mantenha o `.env` cadastrado no painel (não versionado) e habilite “Recriar containers” no redeploy para garantir que novas imagens sejam aplicadas.

## Erros comuns e como corrigir
- **"unable to prepare context: path .../users-service not found"**: confirme que o repositório foi clonado na raiz configurada no Easypanel (campo “Caminho de Build” = `/`) e que o Compose usado é o `docker-compose.prod.yml` da raiz. O arquivo já referencia os Dockerfiles via caminho absoluto relativo à raiz (`dockerfile: users-service/Dockerfile` e `dockerfile: api-gateway/Dockerfile`), então não é necessário mover os serviços para outra pasta.
