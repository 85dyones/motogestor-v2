# Guia: Deploy no Easypanel usando build local (compose)

Este guia mostra como usar o EasyPanel para criar uma stack que *constrói* as imagens a partir
do código do repositório (modo `build:` no docker-compose). É a alternativa quando você não
quer publicar imagens em um registry (ou quando o registry requer autenticação que você não quer
configurar). As alterações deste repositório já incluem um `docker-compose.easypanel.yml` pré-configurado
para `build:`.

## Vantagens do modo `build:`
- Não depende de um registry público/privado (nenhum pull externo requerido).
- Mantém imagens alinhadas ao código do repositório — útil para deploys diretos do código.

## Considerações / pré-requisitos
- O EasyPanel (host) precisa clonar ou ter acesso ao código do repositório antes de executar o `docker compose`.
- Builds podem demorar e consumir CPU/RAM — configure limites de recursos no painel se possível.
- Se o projeto depende de variáveis sensíveis use os `secrets` ou variáveis de ambiente do painel em vez do `.env` commitado.

## Exemplo: arquivo `docker-compose.easypanel.yml`

O repositório já contém um arquivo preparado para Easypanel (`docker-compose.easypanel.yml`). Nele os serviços
constroem imagens a partir dos contextos apropriados, por exemplo:

```yaml
users-service:
  build:
    context: ./users-service
    dockerfile: Dockerfile
  env_file: [.env]
  environment:
    APP_ENV: production
    # ... outras variáveis

# api-gateway, financial-service, management-service, teamcrm-service, ai-service
# estão configurados de forma análoga para build local.
```

## Passo a passo no EasyPanel (modo build)
1. No EasyPanel, crie uma nova stack e aponte para o repositório contendo o `docker-compose.easypanel.yml`.
2. Configure variáveis e secrets no painel (no lugar de deixar segredos no `.env` no repo).
3. Suba a stack usando o compose (o painel normalmente executa `docker compose up --build -d`):

```bash
docker compose -f docker-compose.easypanel.yml up --build -d
```

4. Monitore a saída de build dos serviços no painel. Corrija erros de build (dependências, permissões, etc.) conforme necessário.

## Debug — erros comuns e como resolver
- Erro: `denied` ao puxar imagens — significa que o host tentou `pull` de um registry privado. Solução: usar `build:` ou fornecer credenciais (`docker login ghcr.io`) no host/painel.
- Erro: builds muito lentos / falhando por falta de memória — aumente recursos do host ou limite paralelismo de build.
- Verifique se todos os Dockerfiles estão presentes nos diretórios correspondentes (ex: `users-service/Dockerfile`).

## Alternativa: usar imagens no registry (GHCR)
- Se preferir publicar imagens e usar `image:` no compose, publique as imagens no GHCR como `ghcr.io/<org>/<name>:tag` e garanta que o host esteja autenticado com `docker login ghcr.io` ou configure as credenciais no painel.

## Segurança e versionamento
- Para controle de versões, prefira usar tags fixas (`:v1.2.3`) ao invés de `:latest` em produção quando utilizar registries.
- Para builds locais, configure pipelines CI para gerar imagens e publicar releases caso deseje deploys mais reprodutíveis.

## Observações finais
Se quiser, posso:
- abrir uma PR com todas as alterações aplicadas (compose + docs) — já fiz as mudanças locais e posso publicar a branch;
- adicionar checagens/CI para validar que `docker-compose.easypanel.yml` constrói corretamente no CI (opcional).
