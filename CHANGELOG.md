# Changelog

## 2.0.0

- Corrige TemplateResponse con Starlette actual y elimina el HTTP 500 del dashboard.
- Reemplaza self-test de introspección defectuosa por pruebas HTTP reales.
- API v1 versionada y compatibilidad temporal con rutas antiguas.
- PolicyEngine, RBAC y ApprovalService de un solo uso.
- Auditoría persistente SQLite y logging JSONL.
- Microsoft Device Code Flow con cache cifrada.
- Google OAuth callback con token cifrado.
- GitHub token validation, repos, workflows y branch control.
- Integrations status normalizado.
- Errores globales estructurados.
- Correlation ID, rate limiting y trusted hosts/CORS.
- Retry/backoff/circuit breaker para APIs HTTP externas.
- Dashboard/UI Graphite + Steel Blue.
- Scheduler persistente y automation history.
- Tareas/recordatorios persistentes y task history.
- Tests unitarios, integración, seguridad y E2E.
