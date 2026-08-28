# Configuración REAL

## 1. Instalar

PowerShell:

    .\scripts\install_windows.ps1

## 2. Microsoft Outlook / Calendar / Teams

En Microsoft Entra admin center:

1. App registrations -> New registration.
2. Tipo de cuenta: organización según tu tenant. Para uso multitenant, usa el tenant apropiado.
3. Copia Application (client) ID a `MS_CLIENT_ID`.
4. Authentication -> Allow public client flows = Yes.
5. API permissions -> Microsoft Graph -> Delegated permissions:
   - User.Read
   - Mail.Read
   - Mail.Send
   - Calendars.ReadWrite
   - Chat.Read
   - Team.ReadBasic.All
   - Channel.ReadBasic.All
6. Para leer mensajes de canales de Teams agrega `ChannelMessage.Read.All` y obtén consentimiento de administrador. Luego pon `MS_ENABLE_TEAMS_CHANNELS=true`.
7. No agregues client secret para este flujo de escritorio.

Inicia el servidor y ejecuta POST `/auth/microsoft/device-login` desde Swagger. Sigue el código de dispositivo mostrado por Microsoft.

## 3. Gmail / Google Calendar

1. Crea un proyecto en Google Cloud.
2. Habilita Gmail API y Google Calendar API.
3. Configura OAuth consent screen.
4. Crea OAuth Client ID tipo Desktop app.
5. Descarga JSON como `secrets/google_credentials.json`.
6. Ejecuta POST `/auth/google/login`.
7. Autoriza los scopes solicitados.

## 4. GitHub

Para uso personal, crea un fine-grained token con solo los repositorios y permisos necesarios. Ponlo en `.env` como `GITHUB_TOKEN`. Nunca lo subas a Git.

## 5. Uso

Servidor:

    .\scripts\run_windows.ps1

Swagger:

    http://127.0.0.1:8000/docs

Ejemplos:

- `mail/list_unread` con `source=microsoft` o `source=google`.
- `calendar/list_events`.
- `calendar/create_event` con `approved=true`.
- `meeting/list_chats` y `meeting/chat_messages`.
- `meeting/channel_messages` solo con permiso administrativo correspondiente.
- `development/github_repos`.
- `monitoring/system_health`.
- `security/scan_secrets`.
- `database/sqlite_integrity`.
- `reminder/create_reminder`.

## Política de seguridad

READ: automático.
PREPARE: puede ejecutar análisis local controlado.
WRITE: requiere `approved=true`.
DANGEROUS: bloqueado.

No guardes contraseñas de Outlook, Gmail o Teams en `.env`. Se usan tokens OAuth.


## Flujo Microsoft Device Code corregido (v1.0.1)

1. Configura `MS_CLIENT_ID` en `.env`.
2. En Swagger ejecuta `POST /auth/microsoft/device-login`.
3. La respuesta entrega `user_code`, `verification_uri` y `job_id` inmediatamente.
4. Abre `verification_uri`, ingresa `user_code` y autentícate.
5. Consulta `GET /auth/microsoft/device-login/status/{job_id}` hasta obtener `status: authenticated`.
6. Verifica con `GET /auth/microsoft/me`.

El registro de aplicación de Microsoft Entra debe permitir Public Client Flow para Device Code.


## 6. Interfaz profesional 1.1.0

Dashboard: `http://127.0.0.1:8000/`

Vistas:

- `/ui/agents`
- `/ui/integrations`
- `/ui/automations`
- `/ui/tasks`
- `/ui/monitoring`
- `/ui/audit`
- `/ui/settings`

Swagger se conserva en `/docs` como catálogo técnico y consola de pruebas de la API.
OpenAPI permanece en `/openapi.json`.

Las automatizaciones recurrentes solo admiten acciones READ y PREPARE. Las acciones WRITE requieren aprobación interactiva y DANGEROUS permanece bloqueado.
