# Observabilidade no MotoGestor v2

## 3.1 Logs estruturados
- Formato JSON padrão com campos: `timestamp`, `level`, `service`, `message`, `tenant_id`, `trace_id`, `route`.
- Middleware gera/propaga `X-Trace-Id` por requisição e injeta em `g.trace_id` para ser usado pelo logger e pelos spans.
- Configuração aplicada via `register_observability(app, service_name)` em cada serviço Flask.
- Exemplo de log:
```json
{"timestamp":"2024-09-10T12:00:00+0000","level":"INFO","service":"users-service","message":"login succeeded","trace_id":"2f5c...","tenant_id":42,"route":"/auth/login"}
```

### Integração com Gunicorn
Em `wsgi.py` o `create_app()` já registra o middleware e a configuração de logging. Inicie o Gunicorn passando `--access-logfile -` para manter os access logs no stdout e unificar nos collectors:
```bash
gunicorn --bind 0.0.0.0:8000 wsgi:app --workers 4 --access-logfile -
```

## 3.2 Métricas Prometheus
- `/metrics` exposto em todos os serviços via `prometheus_flask_exporter`.
- Métricas customizadas:
  - `http_request_latency_seconds{service,method,route}`
  - `http_requests_total{service,method,route,status}`
  - `auth_errors_total{service}`
  - `os_created_total{tenant_id}` (aplicado no management-service ao criar OS).
- Latência e contagem são alimentadas pelo middleware `after_request` que usa `g.route_label` e `g.trace_id`.

### docker-compose.observability.yml
Arquivo sugerido na raiz para subir Prometheus + Grafana já apontando para os endpoints dos serviços Flask.

## 3.3 Tracing com OpenTelemetry
- Habilitado opcionalmente quando `OTEL_EXPORTER_OTLP_ENDPOINT` está definido.
- `register_observability` inicializa o `TracerProvider` com `service.name` e exporta via OTLP/HTTP (respeita `OTEL_EXPORTER_OTLP_INSECURE=true|false`).
- `FlaskInstrumentor` e `RequestsInstrumentor` propagam contexto HTTP entre gateway e micro-serviços.
- O middleware adiciona atributos nos spans atuais: `tenant.id`, `http.route`, `http.trace_id`.
- Exportar para collector:
```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318/v1/traces \
OTEL_EXPORTER_OTLP_INSECURE=true \
flask run
```

## Referências rápidas
- Trace ID propagado em `X-Trace-Id` em todas as respostas.
- Logs e métricas usam `g.current_tenant_id` preenchido pelo `tenant_guard`.
- Prometheus/Grafana podem ser ligados pelo compose sugerido e apontar para as portas 5001..5006 conforme os serviços expõem.
