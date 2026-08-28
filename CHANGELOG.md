# Changelog

## 1.1.0

- Dashboard profesional en `/`.
- UI de agentes en `/ui/agents`.
- UI de integraciones en `/ui/integrations`.
- UI de automatizaciones en `/ui/automations`.
- UI de tareas y recordatorios en `/ui/tasks`.
- UI de monitoreo en `/ui/monitoring`.
- UI de auditoría en `/ui/audit`.
- UI de configuración en `/ui/settings`.
- Swagger conservado en `/docs`.
- OpenAPI conservado en `/openapi.json`.
- Tema Graphite / Steel Blue con fondo gris grafito, paneles oscuros y acentos azul acero.
- Ejecutor visual de agentes con niveles READ/PREPARE/WRITE/DANGEROUS.
- Automatizaciones persistentes en SQLite para acciones READ/PREPARE.
- Scheduler de automatizaciones con APScheduler.
- Estado dinámico de agentes e integraciones.
- Flujo visual Microsoft Device Code con polling de estado.
- Verificación visual Microsoft, Google y GitHub.
- Monitoreo dinámico CPU/RAM/disco/procesos.
- Comprobación TCP desde UI.
- Arranque de Windows separado en instalación, inicio normal y reparación forzada.
- Self-test corregido para ejecución directa desde `scripts`.
- Router determinístico ampliado para correo, calendario, Teams, tareas, recordatorios, seguridad, GitHub y monitoreo.
