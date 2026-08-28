# HAGUER Agent Platform REAL UI 1.1.0

Plataforma local de agentes para productividad e Ingeniería en Informática.

## Interfaz

- `/` Dashboard profesional.
- `/ui/agents` Administración y ejecución de agentes.
- `/ui/integrations` Microsoft 365 / Google Workspace / GitHub.
- `/ui/automations` Automatizaciones READ/PREPARE.
- `/ui/tasks` Tareas y recordatorios.
- `/ui/monitoring` CPU / RAM / disco / TCP.
- `/ui/audit` Auditoría.
- `/ui/settings` Configuración no sensible.
- `/docs` Swagger técnico.
- `/openapi.json` OpenAPI.

## Agentes

Orchestrator + 13 agentes especializados: Mail, Calendar, Teams/Meeting, Task, Reminder, Follow-up, Development, DevOps, Security, Database, Documentation, Monitoring y Knowledge.

## Instalar en Windows

Desde `C:\DEV\AGENTES`:

    .\INSTALAR_AGENTES.cmd

Luego iniciar normalmente:

    .\INICIAR_AGENTES.cmd

Abrir:

    http://127.0.0.1:8000/

Swagger permanece en:

    http://127.0.0.1:8000/docs

## Seguridad

- READ: automático.
- PREPARE: análisis/preparación.
- WRITE: exige aprobación explícita.
- DANGEROUS: bloqueado.
- Las automatizaciones recurrentes no pueden ejecutar WRITE/DANGEROUS.
- `.env`, tokens OAuth y secretos están ignorados por Git.

Consulta `SETUP_REAL.md` para Microsoft, Google y GitHub.
