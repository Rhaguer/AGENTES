# HAGUER Agent Platform REAL

Versión ejecutable de una plataforma de agentes para un Ingeniero en Informática.

No es una maqueta: los conectores implementan llamadas reales a Microsoft Graph, Gmail/Google Calendar y GitHub una vez configurado OAuth/tokens.

Incluye 14 componentes/agentes:
- Orchestrator
- Mail
- Calendar
- Meeting/Teams
- Task
- Reminder
- Follow-up
- Development/GitHub
- DevOps
- Security
- Database
- Documentation
- Monitoring
- Knowledge

Funciones reales ya implementadas:
- Outlook: correos no leídos y envío.
- Outlook Calendar: lectura y creación de eventos.
- Teams: chats, mensajes de chat, equipos, canales y mensajes de canal (permiso admin para ChannelMessage.Read.All).
- Gmail: correos no leídos y envío.
- Google Calendar: lectura y creación de eventos.
- GitHub: usuario, repositorios y workflow runs.
- Monitor local: CPU, RAM, disco, TCP.
- Git local: inspect, status, tests, commit y push con política de aprobación.
- Seguridad local: búsqueda de posibles secretos.
- SQLite: integridad.
- Tareas y recordatorios persistentes.
- Auditoría en `logs/audit.jsonl`.

Inicio rápido en Windows:

    .\scripts\install_windows.ps1

Luego configura `.env` y sigue `SETUP_REAL.md`.

Ejecuta:

    .\scripts\run_windows.ps1

Abre:

    http://127.0.0.1:8000/docs

Nota: las autorizaciones existentes dentro de ChatGPT no se exportan al programa local. El programa usa su propio OAuth, como corresponde a una aplicación real.
