# 🚀 LLM Microservices Platform — Versión con Text-to-Speech

Este documento es la versión **actualizada** del spec integral, cambiando uno de los microservicios de LLM.  
Antes: `LLM-Summarize` (text summarizer)  
Ahora: `LLM-TextToSpeech` (TTS, usando API Pollinations o equivalente).

---

## 1) Arquitectura (actualizada)

```
[Cliente Web/Móvil]
        │ HTTPS (JWT)
        ▼
   [API Gateway (NestJS)]
   ├── /auth/*        → [Auth & Users | NestJS + PostgreSQL]
   ├── /analytics/*   → [Analytics | FastAPI + MongoDB (NoSQL)]
   ├── /image/*       → [LLM-Image | FastAPI + S3 (llmhist-image-<env>)]
   ├── /tts/*         → [LLM-TextToSpeech | FastAPI + S3 (llmhist-tts-<env>)]
   └── /chat/*        → [LLM-Chat | FastAPI + S3 (llmhist-chat-<env>)]
                    (todos reportan eventos a Analytics)
```

---

## 2) Contratos de API (microservicios)

### 2.1 Text-to-Speech (FastAPI + S3)

`POST /tts/generate`  
```json
{
  "prompt": "Texto que quiero sintetizar",
  "model": "openai-audio",
  "voice": "alloy"
}
```
**Response**:
```json
{
  "id": "req_tts_123",
  "s3": {
    "record": "requests/2025/10/01/req_tts_123/record.json",
    "audio": "requests/2025/10/01/req_tts_123/audio/output.mp3"
  },
  "meta": { "provider": "pollinations", "model": "openai-audio", "voice": "alloy" }
}
```

### 2.2 Otros (sin cambios)
- **Auth (Postgres)**
- **Analytics (MongoDB)**
- **Image (FastAPI + S3)**
- **Chat (FastAPI + S3)**

---

## 3) Historial en S3 (TTS)

**Bucket**: `llmhist-tts-<env>`

**Carpeta por request:**
```
requests/{yyyy}/{mm}/{dd}/{id}/
  ├─ input.json       # prompt + modelo + voz
  ├─ record.json      # metadatos comunes (ver abajo)
  └─ audio/output.mp3 # archivo de audio generado
```

**`input.json` (ejemplo):**
```json
{
  "prompt": "Hola, esto es una prueba",
  "model": "openai-audio",
  "voice": "alloy"
}
```

**`record.json`:**
```json
{
  "id": "req_tts_123",
  "userId": "uuid-user",
  "username": "jane.doe@utec.edu",
  "service": "tts",
  "provider": "pollinations",
  "model": "openai-audio",
  "voice": "alloy",
  "prompt": "Hola, esto es una prueba",
  "status": 200,
  "latencyMs": 1240,
  "cost": { "usd": 0.0018 },
  "artifacts": {
    "audio": "requests/2025/10/01/req_tts_123/audio/output.mp3"
  },
  "createdAt": "2025-10-01T23:30:00.000Z"
}
```

**Índice opcional por usuario:**
```
users/{userId}/tts/history/{yyyy}/{mm}/{dd}.jsonl
```

---

## 4) Analytics (MongoDB)

Los eventos de TTS se registran igual que otros servicios:

```json
{
  "ts": "2025-10-01T23:31:11Z",
  "userId": "uuid-user",
  "username": "jane.doe@utec.edu",
  "service": "tts",
  "action": "generate",
  "requestId": "req_tts_123",
  "provider": "pollinations",
  "model": "openai-audio",
  "latencyMs": 1240,
  "status": 200,
  "tokens": { "in": 25, "out": 0 },
  "cost": { "usd": 0.0018 },
  "meta": { "voice": "alloy" }
}
```

---

## 5) Docker Compose (cambios mínimos)

Agrega un servicio para `svc-llm-tts`:

```yaml
  svc-llm-tts:
    build: ../svc-llm-tts
    env_file: [ ../svc-llm-tts/.env.dev ]
    depends_on: [minio]
```

Y en el Gateway:
```yaml
  gateway:
    environment:
      TTS_URL: http://svc-llm-tts:8000
```

---

## 6) `.env.dev` para TTS

```
PORT=8000
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=minio
S3_SECRET_KEY=minio123
S3_REGION=us-east-1
S3_BUCKET=llmhist-tts-dev
PROVIDER_API_KEY=change-me
```

---

## 7) Frontend (ejemplo de uso)

Formulario sencillo para TTS:
- Input: caja de texto (`prompt`)
- Select: `voice` (`alloy`, `echo`, `fable`, etc.)
- Botón: “Generar Audio”
- Reproduce `signedUrl` del mp3 retornado por el backend.

---

Con esto reemplazamos el microservicio de **Summarizer** por **Text-to-Speech**, manteniendo todo el patrón de historial en S3 + Analytics en Mongo + control vía Gateway. ✅
