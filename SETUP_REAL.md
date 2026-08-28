# Configuración real

## Microsoft 365 / Outlook / Teams

Configura en `.env`:

```text
MS_CLIENT_ID=<Application Client ID>
MS_TENANT_ID=<Tenant ID>
MS_ENABLE_TEAMS_CHANNELS=false
```

La App Registration debe admitir Public Client Flow. Scopes configurados por defecto:

- User.Read
- Mail.Read
- Mail.Send
- Calendars.ReadWrite
- Chat.Read
- Team.ReadBasic.All
- Channel.ReadBasic.All

Para mensajes de canales agrega `ChannelMessage.Read.All`, concede el consentimiento administrativo requerido y después habilita `MS_ENABLE_TEAMS_CHANNELS=true`.

Flujo:

1. `POST /auth/microsoft/device-login`.
2. Abre `verification_uri` e ingresa `user_code`.
3. Consulta `GET /auth/microsoft/device-login/status/{job_id}`.
4. Verifica con `GET /auth/microsoft/me`.

Sin configuración devuelve 503; sin sesión válida devuelve 401. No debe producir 500 por credenciales ausentes.

## Google Workspace

1. Habilita Gmail API y Google Calendar API.
2. Configura OAuth consent screen.
3. Crea OAuth Client y descarga el JSON.
4. Guarda el archivo como `secrets/google_credentials.json`.
5. Ejecuta `POST /auth/google/login`.
6. Abre `authorization_url`.
7. Google redirige a `/auth/google/callback` y el token queda cifrado localmente.
8. Verifica con `GET /auth/google/me`.

Scopes: Gmail readonly/send y Calendar readonly/events.

## GitHub

Configura un fine-grained token con mínimo privilegio:

```text
GITHUB_TOKEN=<token>
```

Verifica con:

```text
GET /auth/github/me
```

La UI permite conectar/habilitar, probar y desconectar lógicamente sin eliminar el token del entorno.

## Aprobaciones

Para WRITE/DANGEROUS:

1. `POST /api/v1/approvals/request` con agente, acción y payload exacto.
2. `POST /api/v1/approvals/{id}/decision` con `approve`.
3. La respuesta entrega un `approval_token` de un solo uso.
4. Ejecuta la acción con `approval_id` + `approval_token`.

Una aprobación expirada, reutilizada, de otro actor o con payload/acción/target distinto es rechazada.

## RBAC

Headers soportados en despliegue local/proxy:

```text
X-Actor: usuario
X-Role: READ_ONLY | USER | OPERATOR | ADMIN
X-Correlation-ID: opcional
```

En production configura un proxy/SSO que establezca estos headers de forma confiable. No expongas el servicio productivo directamente aceptando headers aportados por Internet.

## Producción

Copia `config/production.env.example` a `config/production.env` y ajusta:

- DEBUG=false.
- Trusted Hosts explícitos.
- CORS restringido.
- `DEFAULT_ROLE=READ_ONLY`.
- `APPROVAL_REQUIRE_DIFFERENT_ACTOR=true`.
- `HAGUER_MASTER_KEY` inyectada desde un gestor de secretos.
- OAuth redirect URIs reales.
- Base de datos, backup y logging según infraestructura.

Rota credenciales invalidando tokens en los proveedores, desconectando la integración y generando credenciales nuevas. Nunca registres tokens en Git.
