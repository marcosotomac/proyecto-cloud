# 🚀 LLM Microservices Platform

Plataforma de microservicios para APIs LLM con autenticación JWT, almacenamiento S3 y analíticas.

## 🏗️ Arquitectura

```
[Cliente Web/Móvil]
        │ HTTPS (JWT)
        ▼
   [API Gateway] (Futuro)
   ├── /auth/*        → [Users Service | NestJS + PostgreSQL]
   ├── /image/*       → [Text-to-Image | FastAPI + S3]
   ├── /tts/*         → [Text-to-Speech | FastAPI + S3]
   ├── /summarize/*   → [Summarizer] (Futuro)
   └── /chat/*        → [Chat] (Futuro)
```

## 🎯 Servicios Implementados

### ✅ Users/Auth Service (NestJS)

- **Puerto:** 3000
- **Base de datos:** PostgreSQL
- **Características:**
  - Registro y login de usuarios
  - Autenticación JWT con refresh tokens
  - Gestión de sesiones
  - Endpoints protegidos

### ✅ Text-to-Image Service (FastAPI)

- **Puerto:** 8000
- **Almacenamiento:** S3/MinIO
- **Proveedor:** Pollinations.ai
- **Características:**
  - Generación de imágenes con IA
  - Historial en S3 con metadatos
  - Soporte para usuarios autenticados y anónimos
  - URLs firmadas para descarga

### ✅ Text-to-Speech Service (FastAPI)

- **Puerto:** 8001
- **Almacenamiento:** S3/MinIO
- **Proveedor:** gTTS (Google Text-to-Speech)
- **Características:**
  - Síntesis de voz de texto a audio
  - Múltiples idiomas (en, es, fr, de, it, pt, ja, zh-CN, etc.)
  - Modelos: gtts (normal), gtts-slow (lento)
  - Historial en S3 con metadatos
  - Soporte para usuarios autenticados y anónimos
  - URLs firmadas para descarga de audio MP3

## 🚀 Inicio Rápido

### 1. Levantar toda la plataforma

```bash
# Construir y levantar servicios
make up-build

# Ver estado
make status

# Ver logs
make logs
```

### 2. Probar autenticación

```bash
# Registrar usuario
curl -X POST "http://localhost:3000/auth/register" \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"password123"}'

# Iniciar sesión (guarda el accessToken)
curl -X POST "http://localhost:3000/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"password123"}'
```

### 3. Generar imagen (anónimo)

```bash
curl -X POST "http://localhost:8000/image/generate" \
     -H "Content-Type: application/json" \
     -d '{"prompt":"cyberpunk cat with neon lights","size":"512x512"}'
```

### 4. Generar imagen (autenticado)

```bash
curl -X POST "http://localhost:8000/image/generate" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -d '{"prompt":"authenticated image","size":"512x512"}'
```

### 5. Generar audio (anónimo)

```bash
# Inglés
curl -X POST "http://localhost:8001/tts/generate" \
     -H "Content-Type: application/json" \
     -d '{"prompt":"Hello, this is a test of text to speech","voice":"en","model":"gtts"}'

# Español
curl -X POST "http://localhost:8001/tts/generate" \
     -H "Content-Type: application/json" \
     -d '{"prompt":"Hola, esto es una prueba","voice":"es","model":"gtts"}'
```

### 6. Generar audio (autenticado)

```bash
curl -X POST "http://localhost:8001/tts/generate" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -d '{"prompt":"authenticated audio","voice":"en","model":"gtts"}'
```

### 7. Acceder a endpoint protegido

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     "http://localhost:8000/admin/images"
```

## 📡 APIs Disponibles

### Users/Auth Service (Puerto 3000)

```bash
POST /auth/register     # Registrar usuario
POST /auth/login        # Iniciar sesión
POST /auth/refresh      # Renovar tokens
POST /auth/logout       # Cerrar sesión
GET  /users/me          # Perfil usuario (protegido)
```

### Text-to-Image Service (Puerto 8000)

```bash
POST /image/generate           # Generar imagen
GET  /image/{id}              # Info de imagen
GET  /image/{id}/download     # URL descarga
GET  /admin/images            # Lista imágenes (protegido)
GET  /healthz                 # Health check
```

### Text-to-Speech Service (Puerto 8001)

```bash
POST /tts/generate            # Generar audio
GET  /tts/{id}               # Info de audio
GET  /tts/{id}/download      # URL descarga audio
GET  /admin/audios           # Lista audios (protegido)
GET  /healthz                # Health check
```

## 🗄️ Almacenamiento

### PostgreSQL (Puerto 5432)

- **Usuario:** postgres
- **Contraseña:** postgres
- **Tablas:** users, sessions

### MinIO (Puertos 9000/9001)

- **Console:** http://localhost:9001
- **Usuario:** minio
- **Contraseña:** minio123
- **Buckets:**
  - llmhist-image-dev (Text-to-Image)
  - llmhist-tts-dev (Text-to-Speech)

### Estructura S3 - Text-to-Image

```
llmhist-image-dev/
├── requests/{yyyy}/{mm}/{dd}/{id}/
│   ├── input.json      # Parámetros entrada
│   ├── record.json     # Metadatos completos
│   └── image/original.png # Imagen generada
└── users/{userId}/image/history/
    └── {yyyy}/{mm}/{dd}.jsonl # Índice por usuario
```

### Estructura S3 - Text-to-Speech

```
llmhist-tts-dev/
├── requests/{yyyy}/{mm}/{dd}/{id}/
│   ├── input.json      # Parámetros entrada (prompt, voice)
│   ├── record.json     # Metadatos completos
│   └── audio/output.mp3 # Audio generado
└── users/{userId}/tts/history/
    └── {yyyy}/{mm}/{dd}.jsonl # Índice por usuario
```

## 🛠️ Comandos Útiles

```bash
# Construcción y despliegue
make build              # Construir imágenes
make up                 # Levantar servicios
make down               # Detener servicios
make clean              # Limpiar todo

# Logs y debugging
make logs               # Ver todos los logs
make logs-users         # Logs servicio usuarios
make logs-image         # Logs servicio imágenes
make logs-speech        # Logs servicio text-to-speech
make healthcheck        # Verificar salud servicios

# Testing
make test-auth          # Probar autenticación
make test-image         # Probar generación imagen
make test-speech        # Probar generación audio
make test-protected     # Probar endpoint protegido

# Desarrollo
make dev-users          # Ejecutar users en dev
make dev-image          # Ejecutar image en dev
make dev-speech         # Ejecutar speech en dev
make setup-dev          # Configurar .env files
```

## 🔧 Desarrollo Local

### Requisitos

- Docker & Docker Compose
- Node.js 18+ (para users service)
- Python 3.11+ (para image y speech services)
- pnpm (para users service)

### Setup

```bash
# Clonar e instalar
git clone <repo>
cd llm-microservices

# Configurar entorno
make setup-dev

# Instalar dependencias
make install-deps

# Levantar servicios
make up-build
```

## 🔐 Autenticación

La plataforma usa **JWT con refresh tokens**:

1. **Registro/Login** → `accessToken` (15min) + `refreshToken` (30d)
2. **Headers** → `Authorization: Bearer <accessToken>`
3. **Renovación** → `POST /auth/refresh` con `refreshToken`
4. **Logout** → Revoca la sesión del `refreshToken`

## 📊 Próximas Características

- [ ] **API Gateway** (NestJS)
- [ ] **Analytics Service** (FastAPI + MongoDB)
- [ ] **Summarizer Service** (FastAPI + S3)
- [ ] **Chat Service** (FastAPI + S3)
- [ ] **Frontend Dashboard** (React/Next.js)
- [ ] **Rate Limiting**
- [ ] **Métricas Prometheus**

## 🚨 Troubleshooting

### Servicios no inician

```bash
# Verificar estado
make status

# Ver logs específicos
make logs-users
make logs-image

# Limpiar y reiniciar
make clean
make up-build
```

### Errores de autenticación

```bash
# Verificar users service
curl http://localhost:3000/

# Verificar JWT token válido
curl -H "Authorization: Bearer TOKEN" http://localhost:3000/users/me
```

### Problemas con S3/MinIO

```bash
# Acceder a MinIO Console
open http://localhost:9001

# Verificar bucket existe
docker exec llm-minio mc ls minio/llmhist-image-dev/
```

## 📝 Notas de Producción

- [ ] Usar secretos seguros para JWT
- [ ] Configurar HTTPS/TLS
- [ ] Implementar rate limiting
- [ ] Configurar logs centralizados
- [ ] Establecer monitoreo
- [ ] Backup de bases de datos
