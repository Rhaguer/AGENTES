# HAGUER Agent Platform 2.0.0

Plataforma local de agentes para productividad e Ingeniería en Informática, con UI operativa, API FastAPI versionada, Swagger, OAuth, RBAC, aprobaciones de un solo uso, auditoría SQLite, automatizaciones y monitoreo.

## URLs

- `http://127.0.0.1:8000/` Dashboard operativo.
- `/ui/agents` Agentes.
- `/ui/integrations` Microsoft / Google / GitHub.
- `/ui/automations` Scheduler y JobStore.
- `/ui/tasks` Tareas y recordatorios.
- `/ui/monitoring` Salud y latencia.
- `/ui/audit` Auditoría persistente.
- `/ui/settings` Configuración saneada.
- `/docs` Swagger técnico.
- `/openapi.json` contrato OpenAPI.
- `/api/v1/*` API estable v1.

## Agentes

Orchestrator + Mail, Calendar, Teams/Meeting, Task, Reminder, Follow-up, Development, DevOps, Security, Database, Documentation, Monitoring y Knowledge.

## Seguridad

- READ: directo según RBAC.
- PREPARE: no modifica recursos; READ_ONLY no lo ejecuta.
- WRITE: requiere aprobación de un solo uso.
- DANGEROUS: solo ADMIN y siempre requiere aprobación de un solo uso.
- `approved:true` no tiene efecto y no aparece en el contrato OpenAPI.
- La aprobación se vincula a actor + agente + acción + target + SHA-256 de parámetros.
- Tokens Microsoft/Google se almacenan cifrados con Fernet.
- `.env`, tokens, claves y credenciales están excluidos por `.gitignore`.
- Cada request tiene `X-Correlation-ID` y cada ejecución se registra en SQLite.

## Instalación Windows

Desde `C:\DEV\AGENTES`:

```powershell
.\INSTALAR_AGENTES.cmd
```

Para iniciar:

```powershell
.\INICIAR_AGENTES.cmd
```

No es necesario activar `.venv` manualmente.

## Validación

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\selftest.py
```

Consulta `SETUP_REAL.md` para OAuth y `IMPLEMENTATION_STATUS.md` para el detalle del checklist.
