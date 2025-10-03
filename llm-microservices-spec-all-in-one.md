# 🚀 Plataforma LLM Microservices — Especificación Integral (*Vibe Coding Ready*)

**Objetivo:** Implementar una app con **5 microservicios** + **API Gateway** que usa **APIs LLM** (text-to-image, summarizer, chat), con **historial por servicio en S3**, **Auth/Users** en **PostgreSQL**, **Analytics** en **MongoDB (NoSQL)**, y un **dashboard** de uso por usuario.

---

## 0) TL;DR (arranque en 5 pasos)

```bash
# 1) Clona y crea llaves/envs
make init   # (genera .env.dev y llaves JWT para dev)

# 2) Levanta DEV (Postgres, Mongo, MinIO + servicios + gateway)
docker compose -f infra/docker-compose.yml up --build

# 3) Registra y loguéate (JWT)
http :8080/auth/register email=test@dev.com password=secret123
http :8080/auth/login email=test@dev.com password=secret123

# 4) Usa LLMs (se guarda historial en S3 y eventos en Analytics)
http :8080/summarize text='Explica fiebre amarilla en 5 bullets' length=short
http :8080/chat/session
http :8080/chat/message sessionId=demo messages:='[{"role":"user","content":"Hola"}]'
http :8080/image/generate prompt='alpaca cyberpunk'

# 5) Dashboard por usuario
http :8080/analytics/user/<USER_ID>/overview
http :8080/analytics/user/<USER_ID>/timeseries bucket==day
```

---

## 1) Arquitectura

```
[Cliente Web/Móvil]
        │ HTTPS (JWT)
        ▼
   [API Gateway (NestJS)]
   ├── /auth/*        → [Auth & Users | NestJS + PostgreSQL]
   ├── /analytics/*   → [Analytics | FastAPI + MongoDB (NoSQL)]
   ├── /image/*       → [LLM-Image | FastAPI + S3 (llmhist-image-<env>)]
   ├── /summarize/*   → [LLM-Summarize | FastAPI + S3 (llmhist-summarize-<env>)]
   └── /chat/*        → [LLM-Chat | FastAPI + S3 (llmhist-chat-<env>)]
                    (todos reportan eventos a Analytics)
```

**Claves de diseño**
- **Auth** en **PostgreSQL** · **Analytics** en **MongoDB (NoSQL)**.
- **Un bucket S3 por servicio LLM** (historial). Acceso *mínimo* por IAM Role.
- **Gateway**: JWT, CORS, rate-limit, `X-User-Id` y `X-Request-Id` propagados.
- **Privacidad**: puedes guardar `promptHash` en vez de `prompt` literal.

---

## 2) Contratos de API (OpenAPI-lite)

### 2.1 Auth & Users (NestJS + Postgres)
- `POST /auth/register` → `{ email, password }` → `{ user, accessToken, refreshToken }`
- `POST /auth/login` → `{ email, password }` → `{ accessToken, refreshToken }`
- `POST /auth/refresh` → `{ refreshToken }` → `{ accessToken, refreshToken }`
- `POST /auth/logout` → 204
- `GET /users/me` → `{ id, email, role, createdAt }`

### 2.2 Analytics (FastAPI + MongoDB)
- `POST /analytics/events` → cuerpo = documento de evento (ver §5).
- `GET /analytics/user/:userId/overview?from&to`
- `GET /analytics/user/:userId/timeseries?from&to&bucket=day|hour`
- `GET /analytics/user/:userId/perf?from&to`
- `GET /analytics/user/:userId/costs?from&to`

### 2.3 LLM-Image (FastAPI + S3)
- `POST /image/generate` `{ prompt, size?, seed?, style? }` → `{ id, s3:{record,image,preview?}, meta }`
- `GET /image/:id` → `{ status, s3Keys, meta }`

### 2.4 LLM-Summarize (FastAPI + S3)
- `POST /summarize` `{ text|url|s3Key, length: short|med|long, style? }` → `{ id, s3:{record,summary} }`
- `GET /summarize/:id`

### 2.5 LLM-Chat (FastAPI + S3)
- `POST /chat/session` → `{ sessionId }`
- `POST /chat/message` `{ sessionId, messages[], model? }` → `{ id, sessionId, assistantMessage, s3:{record,output} }`
- `GET /chat/session/:sessionId` → claves S3 del historial

**Headers estándar (Gateway → servicios)**
- `Authorization: Bearer <JWT>` · `X-User-Id: <uuid>` · `X-Request-Id: <uuid>`

---

## 3) Almacenamiento de datos

### 3.1 PostgreSQL (Auth)
```sql
create extension if not exists pgcrypto;

create table users (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  password_hash text not null,
  role text not null default 'user',
  created_at timestamptz not null default now()
);

create table sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id),
  refresh_token_hash text not null,
  user_agent text,
  ip inet,
  created_at timestamptz not null default now(),
  revoked_at timestamptz
);
create index on sessions(user_id);
```

### 3.2 MongoDB (Analytics — colección `events`)

Documento **estándar** de evento:
```json
{
  "_id": "ObjectId",
  "ts": "2025-10-01T22:35:11.901Z",
  "userId": "uuid-usuario",
  "username": "john.doe@acme.com",
  "service": "image|summarize|chat|gateway",
  "action": "generate|summarize|message|...",
  "requestId": "uuid",
  "provider": "pollinations|stability|githubmodels|...",
  "model": "nombre_modelo",
  "latencyMs": 1420,
  "status": 200,
  "tokens": { "in": 0, "out": 0 },
  "size": { "inputBytes": 0, "outputBytes": 0 },
  "cost": { "usd": 0 },
  "meta": { "params": {} }
}
```
**Índices**: `{ userId:1, ts:-1 }`, `{ service:1, ts:-1 }`, `{ requestId:1 }`, TTL opcional en `ts`.

### 3.3 S3 (historial por servicio LLM)

Buckets (uno por servicio):  
- `llmhist-image-<env>` · `llmhist-summarize-<env>` · `llmhist-chat-<env>`

**Carpeta por request (patrón común):**
```
requests/{yyyy}/{mm}/{dd}/{id}/
  ├─ input.json       # entrada limpia o referencia (url/s3Key)
  ├─ record.json      # metadatos comunes (ver §4.1)
  └─ output.json      # salida de proveedor (si aplica)
```

**Índice por usuario (opcional, para listados rápidos):**
```
users/{userId}/{service}/history/{yyyy}/{mm}/{dd}.jsonl  # 1 línea JSON por request
```

#### a) Text-to-Image — artefactos
```
.../image/original.png
.../image/preview.jpg     # opcional
```
`record.json` incluye `artifacts.image` y (opcional) `artifacts.preview`.

#### b) Summarize — artefactos
```
.../summary.txt           # o summary.json si estructurado
```

#### c) Chat — artefactos
```
sessions/{sessionId}/state.json
sessions/{sessionId}/messages/{ts}-{id}.json
```
Se puede **duplicar** el request por turno en `requests/...` con `input.json`/`output.json` + `record.json`.

---

## 4) Esquemas de historial (S3)

### 4.1 `record.json` (común a todos)
```json
{
  "id": "uuid-request",
  "userId": "uuid-user",
  "username": "john.doe@acme.com",
  "service": "image|summarize|chat",
  "provider": "pollinations|githubmodels|...",
  "model": "sdxl|gpt-4o-mini|...",
  "prompt": "texto del prompt o hash",
  "promptHash": "sha256:...",
  "status": 200,
  "latencyMs": 1640,
  "tokens": { "in": 1200, "out": 350 },
  "size": { "inputBytes": 8421, "outputBytes": 1048576 },
  "cost": { "usd": 0.0032 },
  "createdAt": "2025-10-01T22:40:00.000Z",
  "artifacts": { "image": "requests/.../image/original.png" },
  "meta": { "params": { "size":"1024x1024" } }
}
```

### 4.2 `input.json` por servicio
- **Image**: `{ "prompt": "...", "size":"1024x1024", "seed":123, "style":"photoreal" }`
- **Summarize**: `{ "text|url|s3Key": "...", "length":"short|med|long", "style?": "bullet" }`
- **Chat**: `{ "sessionId": "...", "messages": [...], "tools?": [...] }`

### 4.3 Respuestas API incluyendo claves S3
- **Image**:
```json
{
  "id": "7a1c...",
  "s3": {
    "record": "requests/2025/10/01/7a1c.../record.json",
    "image": "requests/2025/10/01/7a1c.../image/original.png",
    "preview": "requests/2025/10/01/7a1c.../image/preview.jpg"
  }
}
```
- **Summarize**:
```json
{ "id": "cf0e...", "s3": { "record": "requests/.../record.json", "summary": "requests/.../summary.txt" } }
```
- **Chat**:
```json
{ "id": "req_8b2a...", "sessionId": "chat_123", "s3": { "record": "requests/.../record.json", "output": "requests/.../output.json" } }
```

---

## 5) Analytics por usuario (MongoDB)

**KPIs:** usoTotal, serviciosDistintos, topServicios, topModelos, p50/p95 latencia, errorRate, consumo (tokens/bytes/usd), series por día/hora.

### 5.1 Pipelines listos
- **Overview (360°):**
```javascript
db.events.aggregate([
  { $match: { userId: "<uuid>", ts: { $gte: ISODate("2025-09-01"), $lte: ISODate("2025-10-01") } } },
  { $facet: {
    usoTotal:    [ { $count: "count" } ],
    serviciosSet:[ { $group: { _id: "$service" } }, { $count: "distinct" } ],
    topServicios:[ { $group: { _id: "$service", count: { $sum: 1 } } }, { $sort: { count: -1 } }, { $limit: 5 } ],
    topModelos:  [ { $group: { _id: { provider: "$provider", model: "$model" }, count: { $sum: 1 } } }, { $sort: { count: -1 } }, { $limit: 5 } ],
    latencias:   [ { $group: { _id: null, l: { $push: "$latencyMs" } } }, { $project: { p50: { $percentile: { p: [0.5],  input: "$l" } }, p95: { $percentile: { p: [0.95], input: "$l" } } } } ],
    errores:     [ { $group: { _id: null, total: { $sum: 1 }, err: { $sum: { $cond: [ { $gte: ["$status", 400] }, 1, 0 ] } } } }, { $project: { errorRate: { $cond: [ { $eq: ["$total", 0] }, 0, { $divide: ["$err", "$total"] } ] } } } ],
    consumo:     [ { $group: { _id: null, tokensIn: { $sum: "$tokens.in" }, tokensOut: { $sum: "$tokens.out" }, usd: { $sum: "$cost.usd" } } } ]
  } }
]);
```
- **Serie temporal por servicio (día):**
```javascript
db.events.aggregate([
  { $match: { userId: "<uuid>", ts: { $gte: ISODate("2025-09-01"), $lte: ISODate("2025-10-01") } } },
  { $group: { _id: { day: { $dateTrunc: { date: "$ts", unit: "day" } }, service: "$service" }, count: { $sum: 1 } } },
  { $sort: { "_id.day": 1 } }
]);
```
- **Costos por modelo:**
```javascript
db.events.aggregate([
  { $match: { userId: "<uuid>", ts: { $gte: ISODate("2025-09-01"), $lte: ISODate("2025-10-01") } } },
  { $group: { _id: { service: "$service", provider: "$provider", model: "$model" }, requests: { $sum: 1 }, usd: { $sum: "$cost.usd" }, tokensIn: { $sum: "$tokens.in" }, tokensOut: { $sum: "$tokens.out" } } },
  { $sort: { usd: -1 } }
]);
```

### 5.2 Endpoints (ya definidos en §2.2)
- `/overview`, `/timeseries`, `/perf`, `/costs`

---

## 6) Frontend — Dashboard por usuario (React opcional)
- KPIs (requests, servicios distintos, p95, error rate, coste).
- Barras apiladas (requests/día u hora por servicio).
- Línea de costes por modelo.
- Tablas: top modelos y rendimiento por servicio.
- Env: `NEXT_PUBLIC_ANALYTICS_API_BASE=http://localhost:8080`

> Puedes usar la pantalla **UserAnalyticsDashboard** (shadcn/ui + Recharts) que ya preparamos.

---

## 7) Seguridad y privacidad
- **JWT** RS256, refresh tokens con rotación, revocación en `sessions`.
- **RBAC** simple (`user`, `admin`).
- **Rate limit** por ruta (p.ej. 60 req/min/user).
- **Validación de input**: class-validator (Nest) + Pydantic (FastAPI).
- **Prompts**: opcionalmente guardar **hash** en Analytics/S3 en vez del texto.
- **Signed URLs** S3 con expiración 5–10 min para descargas desde cliente.

---

## 8) Observabilidad
- `X-Request-Id` generado en Gateway, propagado a todos.
- Cada servicio envía `POST /analytics/events` tras cada request LLM.
- `/healthz` en todos los servicios; opcional `/metrics` Prometheus.

---

## 9) Docker & Entorno

### 9.1 Estructura del monorepo
```
/gateway                (NestJS)
/svc-auth               (NestJS + PostgreSQL)
/svc-analytics          (FastAPI + MongoDB client)
/svc-llm-image          (FastAPI)
/svc-llm-summarize      (FastAPI)
/svc-llm-chat           (FastAPI)
/infra                  (compose, Makefile, scripts)
/frontend               (Next.js/React - opcional)
```

### 9.2 `infra/docker-compose.yml`
```yaml
version: "3.9"
services:
  pg:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: postgres
    ports: ["5432:5432"]

  mongo:
    image: mongo:7
    ports: ["27017:27017"]

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minio
      MINIO_ROOT_PASSWORD: minio123
    ports: ["9000:9000","9001:9001"]

  gateway:
    build: ../gateway
    env_file: [ ../gateway/.env.dev ]
    ports: ["8080:8080"]
    depends_on: [svc-auth, svc-analytics, svc-llm-image, svc-llm-summarize, svc-llm-chat]

  svc-auth:
    build: ../svc-auth
    env_file: [ ../svc-auth/.env.dev ]
    depends_on: [pg]

  svc-analytics:
    build: ../svc-analytics
    env_file: [ ../svc-analytics/.env.dev ]
    depends_on: [mongo]

  svc-llm-image:
    build: ../svc-llm-image
    env_file: [ ../svc-llm-image/.env.dev ]
    depends_on: [minio]

  svc-llm-summarize:
    build: ../svc-llm-summarize
    env_file: [ ../svc-llm-summarize/.env.dev ]
    depends_on: [minio]

  svc-llm-chat:
    build: ../svc-llm-chat
    env_file: [ ../svc-llm-chat/.env.dev ]
    depends_on: [minio]
```

### 9.3 `.env.dev` (plantillas)

**gateway/.env.dev**
```
PORT=8080
JWT_PUBLIC_KEY=-----BEGIN PUBLIC KEY-----...-----END PUBLIC KEY-----
AUTH_URL=http://svc-auth:3000
ANALYTICS_URL=http://svc-analytics:8000
IMAGE_URL=http://svc-llm-image:8000
SUM_URL=http://svc-llm-summarize:8000
CHAT_URL=http://svc-llm-chat:8000
RATE_LIMIT_PER_MIN=60
CORS_ORIGIN=http://localhost:3000
```

**svc-auth/.env.dev**
```
PORT=3000
DATABASE_URL=postgresql://postgres:postgres@pg:5432/postgres
JWT_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----...-----END PRIVATE KEY-----
ACCESS_TTL=900s
REFRESH_TTL=30d
BCRYPT_ROUNDS=10
```

**svc-analytics/.env.dev**
```
PORT=8000
ANALYTICS_MONGO_URI=mongodb://mongo:27017
ANALYTICS_DB=analytics
ANALYTICS_COLLECTION=events
```

**svc-llm-<*>/.env.dev**
```
PORT=8000
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=minio
S3_SECRET_KEY=minio123
S3_REGION=us-east-1
S3_BUCKET=llmhist-<service>-dev  # image|summarize|chat
PROVIDER_API_KEY=change-me
```

---

## 10) IAM y ciclo de vida (S3)

**Política mínima por servicio (ejemplo `image`):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject","s3:GetObject"],
      "Resource": ["arn:aws:s3:::llmhist-image-<env>/*"]
    },
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": ["arn:aws:s3:::llmhist-image-<env>"]
    }
  ]
}
```

**Lifecycle (costos):**
- Mover `artifacts/` a `STANDARD_IA` a 30 días; borrar a 180 días.
- Retener `record.json` y `*.jsonl` ≥ 365 días (o cifrar con KMS).

---

## 11) Snippets clave

**FastAPI (guardar historial en S3 para Image)**
```python
def save_image_history(user, prompt, image_bytes, provider, model, cost_usd=0.0):
  req_id = str(uuid.uuid4()); dt = datetime.utcnow()
  yyyy, mm, dd = dt.strftime("%Y"), dt.strftime("%m"), dt.strftime("%d")
  base = f"requests/{yyyy}/{mm}/{dd}/{req_id}/"
  put_json(base+"input.json", {"prompt": prompt})
  put_bytes(base+"image/original.png", image_bytes, "image/png")
  record = {
    "id": req_id, "userId": user["id"], "username": user["username"],
    "service":"image","provider":provider,"model":model,
    "prompt": prompt, "status":200,"latencyMs":0,"cost":{"usd":cost_usd},
    "artifacts":{"image": base+"image/original.png"},
    "createdAt": dt.isoformat()+"Z"
  }
  put_json(base+"record.json", record)
  # index por usuario (jsonl)
  idx = f"users/{user['id']}/image/history/{yyyy}/{mm}/{dd}.jsonl"
  prev = try_get(idx)  # lee objeto si existe
  put_bytes(idx, (prev + json.dumps({"id": req_id, "record": base+"record.json"}) + "\n").encode(), "application/jsonl")
  return {"id": req_id, "s3": {"record": base+"record.json", "image": base+"image/original.png"}}
```

**Enviar evento a Analytics**
```ts
await fetch(`${ANALYTICS_URL}/analytics/events`, {
  method: 'POST',
  headers: {'content-type':'application/json', 'authorization': req.headers.authorization},
  body: JSON.stringify({
    ts: new Date().toISOString(),
    userId, username, service: 'image', action:'generate', requestId,
    provider, model, latencyMs, status:200,
    tokens: {in:0,out:0}, cost: {usd: costUsd}, meta: { params: payload }
  })
});
```

**Gateway (Nest) — encabezados**
```ts
req.headers['x-request-id'] ||= crypto.randomUUID();
req.headers['x-user-id'] = jwt.sub; // poblado tras validar JWT
```

---

## 12) Checklist final (*vibe coding*)
- [ ] Levantaste `docker compose` y creaste usuario/login
- [ ] Probaste `/summarize`, `/chat/message`, `/image/generate`
- [ ] Verificaste objetos en MinIO (`http://localhost:9001`)
- [ ] Confirmaste `record.json` + artefactos + índices `.jsonl`
- [ ] Viste documentos en MongoDB (`events`)
- [ ] Consultaste `/analytics/user/:id/overview` y series
- [ ] Ajustaste `PROVIDER_API_KEY` y modelos
- [ ] (AWS) Creaste buckets reales + IAM Roles + lifecycle + Secrets

---

Este documento consolida **toda la implementación**: arquitectura, contratos, almacenamiento, analítica, seguridad, Docker/IaC, IAM, lifecycle y snippets para que puedas **codear sin fricción**. ¡A darle! 🔧✨
