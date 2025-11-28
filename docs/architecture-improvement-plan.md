# MotoGestor v2 — Plano de Evolução e Diferenciação

Este documento consolida o que já foi comprometido no repositório e propõe melhorias para levar o produto a um patamar competitivo superior, com foco em multi-tenant robusto, confiabilidade operacional e experiência do cliente.

## 1) Estado atual e compromissos já no código
- Microsserviços Flask (users, management, financial, team/CRM, AI) com API Gateway em Flask e frontend React/Vite.
- Configuração centralizada por serviço (`config.py`), logging estruturado e healthchecks básicos.
- Multi-tenant inicial: `tenant_id` em JWT e scoping nas rotas do `users-service`; gateway repassa contexto de tenant.
- Estrutura para Alembic, pytest, factories e testes de autenticação/seed.
- Docker Compose para dev e prod, com `docker-compose.prod.yml` consumindo `.env` compartilhado, documentação de deploy em Easypanel/Hostinger.

## 2) Multi-tenant nível "hard" (segurança + isolamento)
- **Isolamento de dados**: aplicar scoping obrigatório em ORM/repositories (filtro automático por `tenant_id`) com guard rails que retornam erro se o contexto não existir. Considerar partição lógica por schema (`tenant_{id}`) para clientes premium ou uso de row-level security (RLS) no Postgres.
- **Propagação de contexto**: middleware no gateway que injeta `X-Tenant-ID` e `X-Plan` para todos os serviços, com auditoria de headers exigidos. Rejeitar requisições sem tenant resolvido.
- **Rotação/Revogação de tokens**: introduzir `jti` + tabela de revogação, rotação curta (`exp` curto) e refresh tokens; suportar bloqueio de usuário/tenant em cascata.
- **Auditoria**: trilhas de auditoria por tenant (quem mudou preço, estoque, OS), com exportação para data lake/BI.
- **Recursos premium**: flags por `plan` para liberar automações (n8n), IA assistiva e dashboards avançados.

## 3) Confiabilidade, observabilidade e operações
- **SLOs e healthchecks profundos**: definir SLOs (ex.: auth P99 < 300ms, uptime 99.9%). Healthcheck real por serviço: DB + cache + fila + dependências externas, com status enriquecido.
- **Logs, métricas, traces**: padronizar logging JSON com `trace_id` e `tenant_id`, exportar para Loki/ELK, métricas via Prometheus + Grafana, tracing (OTel) amostrado por tenant/plan.
- **Resiliência**: timeouts e retries com circuit breakers no gateway; fila de dead-letter para jobs (ex.: n8n/AI). Backpressure para evitar saturação em planos básicos.
- **Segurança operacional**: TLS obrigatório entre serviços em produção, varredura de vulnerabilidade (Snyk/Trivy) no CI, rotação de secrets e `JWT_SECRET_KEY` segregado por ambiente.
- **Backups e DR**: backups automáticos do Postgres (dump + PITR se suportado), testes de restauração mensais, runbook de failover e de corrupção de dados.

## 4) Arquitetura de produto e diferenciais
- **Fluxo omnichannel**: integrar WhatsApp/Telegram/telefone no CRM para abertura/atualização de OS e cobrança automática.
- **Oficina inteligente**: IA para orçamento instantâneo (peças + mão de obra) com base em histórico/IA-service; sugestões de upsell e checklists dinâmicos.
- **Automação e no-code**: kits de automações n8n pré-prontas por segmento (delivery, frota, hobby) e catálogo plugável via frontend.
- **Experiência do cliente final**: portal do cliente com rastreio da OS, aprovações rápidas e pagamento integrado.

## 5) Frontend e UX
- **Estados consistentes**: skeletons/loading/empty/error padrão, com toasts centralizados e mensagens de erro mapeadas por código (401/403/409/500).
- **Session/tenant awareness**: `AuthContext` deve armazenar `tenant_id` e `plan`, expor hooks `useTenant` e proteger rotas por feature flag/plan.
- **Componentes reutilizáveis**: biblioteca interna (Card, Layout, Tabela de OS, Steps de orçamento) com design tokens (cores por tenant/tema) e acessibilidade (ARIA/keyboard).
- **Perfomance**: code-splitting por rota, cache SWR/React Query para dados críticos, prefetch de dashboard após login.

## 6) Dados, migrações e QA
- **Governança de dados**: catálogo de dados (dicionário de colunas sensíveis), mascaramento em non-prod, LGPD (opt-in notificações, descarte de dados).
- **Migrações**: pipeline de Alembic com integração no deploy (Easypanel hook), verificador de divergência de schema, migrações idempotentes para seed de tenants demo.
- **Testes**: suite de contrato entre gateway e users; testes e2e mínimos (login, criar OS, faturamento). Fixtures multi-tenant e smoke tests após deploy.

## 7) Roadmap sugerido (curto/médio prazo)
1. **Hardening de multi-tenant** (RLS/guard rails + middleware + refresh tokens) — objetivo: isolamento forte e base para planos.
2. **Observabilidade completa** (logs JSON com trace_id/tenant_id, métricas Prometheus, traces OTel) — objetivo: SLO visível e MTTR baixo.
3. **Frontend resiliente** (estado padrão + erros mapeados + feature flags por plano) — objetivo: UX premium e upsell claro.
4. **Automação e diferenciais** (kits n8n + IA de orçamento) — objetivo: aumentar LTV e efeito wow.
5. **Operação e governança** (backups, DR, segurança CI, catálogo de dados) — objetivo: compliance e previsibilidade.

## 8) Entregáveis recomendados
- PRs curtos e incrementais focados nas prioridades acima, com checklist de: migrações aplicadas, métricas disponíveis, testes de contrato verdes, e screenshot de UX quando aplicável.
- Documentar runbooks (incidentes, rotações de segredo, restauração) e matriz de responsabilidades por serviço (owner, SLO, dashboard, alerta principal).

## 9) Métricas de sucesso
- Redução de incidentes multi-tenant a zero (nenhum vazamento de dados entre oficinas).
- P99 de login e dashboard dentro dos SLOs definidos; erro 5xx < 0.1% em tráfego normal.
- Crescimento de ativação: % de oficinas usando automações n8n e IA de orçamento em 30 dias.
- Tempo médio de resolução de ticket de suporte < 1 dia com observabilidade completa.

