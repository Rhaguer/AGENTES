# Checklist de cierre 2.0.0

1. Microsoft OAuth: implementado; requiere Client ID/Tenant ID reales.
2. Google OAuth: implementado; requiere `google_credentials.json` real.
3. GitHub auth: implementado; requiere token real.
4. WRITE/DANGEROUS: PolicyEngine + ApprovalService de un solo uso.
5. Auditoría: SQLite con campos estructurados y endpoints GET.
6. Orchestrator: registrado y responsable de policy/approval/delegación/audit.
7. `/command`: CommandRouter + IntentClassifier + EntityExtractor + AgentResolver + ActionResolver.
8. Catálogo: modelo AgentInfo completo.
9. Health checks: plataforma y por agente.
10. Integrations status: modelo normalizado sin rutas de secretos.
11. Errores: modelo global `APIError` con correlation ID.
12. OpenAPI: modelos Pydantic y response models en API principal.
13. HTTP: respuestas 400/401/403/404/409/422/424/429/500/503 declaradas.
14. Rate limiting: auth, command, agent execution y WRITE/DANGEROUS.
15. Secretos: `.gitignore`, tokens cifrados, redacción y permisos restrictivos best-effort.
16. RBAC: READ_ONLY/USER/OPERATOR/ADMIN; DANGEROUS sigue exigiendo aprobación.
17. Correlation ID: middleware + orchestrator + audit + logs.
18. Logging estructurado: JSONL con redacción.
19. Timeout/retry/backoff/circuit breaker: Microsoft Graph, Google APIs y GitHub; tratamiento de 429 y 5xx externos.
20. Dashboard: operativo y separado de Swagger.
21. Swagger: conservado en `/docs`.
22. Integraciones: CONNECT/RECONNECT/DISCONNECT/TEST.
23. Agentes: estado, acciones, riesgos, integración, última ejecución, ejecución y audit ID.
24. Monitoreo: API/CPU/RAM/disco/DB/integraciones/agentes/TCP/uptime/errores.
25. Auditoría: filtros por fecha/actor/agente/acción/riesgo/estado/correlation ID.
26. Automatizaciones: scheduler, JobStore SQLite e historial; solo READ/PREPARE.
27. Tareas/recordatorios: persistencia, prioridad, fecha, creador, asignado, completado e historial de tareas.
28. Tests: unit/integration/security/e2e.
29. Tests seguridad: no approval, approved:true, single-use, scope mismatch, RBAC, 404, 422 y rate limit.
30. Production config: development/testing/production examples.
31. `/version`: implementado.
32. API versionada: `/api/v1`; rutas anteriores se mantienen temporalmente.

Dependencias externas no fabricables: IDs OAuth, tenant, consentimiento administrativo, credenciales Google y token GitHub. El programa devuelve 401/503 controlado hasta que esas credenciales sean configuradas.
