# Machine-to-machine API Keys

## Screen

Administrators manage service credentials at:

```text
http://localhost:5173/#/settings/api-keys
```

The complete value is returned and displayed only by the create operation. After
the one-time panel is closed, ALSEMA retains only a SHA-256 hash and the safe
lookup prefix.

## Format and authentication

Keys use the format `alsema_sk_<cryptographically-random-value>` and may be sent
through either header:

```http
Authorization: Bearer alsema_sk_...
```

```http
X-API-Key: alsema_sk_...
```

If both headers are present, they must contain the same key. Values supplied in
`X-API-Key` are never interpreted as user JWTs.

## Initial scopes

- `agents:read`
- `agents:execute`
- `models:read`
- `tasks:read`

Agent execution requires `agents:execute`; listing agents requires
`agents:read`. Model and task reads enforce their respective scopes.

## Administrative API

```text
POST   /api/v1/api-keys
GET    /api/v1/api-keys
DELETE /api/v1/api-keys/{id}
POST   /api/v1/api-keys/{id}/revoke
```

Example creation body:

```json
{
  "name": "instanews-rewriter",
  "scopes": ["agents:read", "agents:execute"],
  "expires_at": null
}
```

The `api_key` response field exists only on `POST /api/v1/api-keys`. List and
later responses expose `key_prefix`, status and timestamps, never the full key.

## InstaNews

Store the key outside source control as `ALSEMA_API_KEY`. A container running on
the same Windows host uses `http://host.docker.internal:8000/api/v1`; a local
non-container process uses `http://localhost:8000/api/v1`.

PowerShell smoke test:

```powershell
$headers = @{ "X-API-Key" = $env:ALSEMA_API_KEY }
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/agents" -Headers $headers
```
