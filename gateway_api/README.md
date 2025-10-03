# API Gateway - LLM Platform

Punto de entrada unificado para todos los microservicios de la plataforma LLM.

## 🚀 Características

- **Proxy Unificado**: Acceso centralizado a todos los microservicios
- **Autenticación JWT**: Gestión de autenticación con JWT HS256
- **Analytics Automático**: Rastreo automático de todas las solicitudes
- **Manejo de Errores**: Gestión robusta de errores y timeouts
- **Health Checks**: Monitoreo del estado de todos los servicios
- **CORS**: Configuración flexible de CORS

## 📋 Arquitectura

El gateway actúa como proxy para los siguientes servicios:

```
Gateway (8080)
├── Users Service (3000) - Autenticación y gestión de usuarios
├── LLM Chat Service (8002) - Chat con GitHub Models
├── Text-to-Image Service (8000) - Generación de imágenes
├── Text-to-Speech Service (8001) - Síntesis de voz
└── Analytics Service (8005) - Análisis de uso
```

## 🔧 Configuración

### Variables de Entorno (.env)

```env
# App
NODE_ENV=development
PORT=8080
LOG_LEVEL=INFO

# JWT
JWT_SECRET_KEY=dev-super-secret-access-key-2024
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Services URLs
USERS_SERVICE_URL=http://users-service:3000
LLM_SERVICE_URL=http://llm-chat-service:8002
IMAGE_SERVICE_URL=http://text-image-service:8000
SPEECH_SERVICE_URL=http://text-speech-service:8000
ANALYTICS_SERVICE_URL=http://analytics-service:8005

# Analytics
ENABLE_ANALYTICS=true

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

## 📡 Endpoints

### Autenticación

| Método | Endpoint             | Descripción         | Auth |
| ------ | -------------------- | ------------------- | ---- |
| POST   | `/api/auth/register` | Registro de usuario | No   |
| POST   | `/api/auth/login`    | Inicio de sesión    | No   |
| POST   | `/api/auth/refresh`  | Renovar token       | No   |
| GET    | `/api/auth/profile`  | Perfil del usuario  | Sí   |

### LLM Chat

| Método | Endpoint                          | Descripción                  | Auth     |
| ------ | --------------------------------- | ---------------------------- | -------- |
| POST   | `/api/chat`                       | Enviar mensaje al chat       | Opcional |
| GET    | `/api/chat/sessions`              | Obtener sesiones del usuario | Sí       |
| GET    | `/api/chat/sessions/{session_id}` | Obtener sesión específica    | Sí       |
| GET    | `/api/chat/models`                | Listar modelos disponibles   | No       |

### Text-to-Image

| Método | Endpoint              | Descripción                | Auth     |
| ------ | --------------------- | -------------------------- | -------- |
| POST   | `/api/image/generate` | Generar imagen             | Opcional |
| GET    | `/api/image/models`   | Listar modelos disponibles | No       |

### Text-to-Speech

| Método | Endpoint               | Descripción              | Auth     |
| ------ | ---------------------- | ------------------------ | -------- |
| POST   | `/api/speech/generate` | Generar audio            | Opcional |
| GET    | `/api/speech/voices`   | Listar voces disponibles | No       |

### Analytics

| Método | Endpoint                                | Descripción            | Auth |
| ------ | --------------------------------------- | ---------------------- | ---- |
| GET    | `/api/analytics/user/me`                | Analytics del usuario  | Sí   |
| GET    | `/api/analytics/service/{service_type}` | Analytics por servicio | No   |
| GET    | `/api/analytics/system`                 | Analytics del sistema  | No   |
| GET    | `/api/analytics/usage`                  | Uso global             | No   |

### Sistema

| Método | Endpoint  | Descripción             | Auth |
| ------ | --------- | ----------------------- | ---- |
| GET    | `/`       | Información del gateway | No   |
| GET    | `/health` | Estado de servicios     | No   |
| GET    | `/docs`   | Documentación Swagger   | No   |
| GET    | `/redoc`  | Documentación ReDoc     | No   |

## 🔐 Autenticación

### Endpoints con Autenticación Obligatoria

- `GET /api/auth/profile`
- `GET /api/chat/sessions`
- `GET /api/chat/sessions/{session_id}`
- `GET /api/analytics/user/me`

### Endpoints con Autenticación Opcional

Los siguientes endpoints funcionan sin autenticación pero rastrean el `user_id` si el token es proporcionado:

- `POST /api/chat`
- `POST /api/image/generate`
- `POST /api/speech/generate`

### Uso del Token JWT

Incluir el token en el header `Authorization`:

```bash
Authorization: Bearer <token>
```

## 📊 Analytics Automático

El gateway automáticamente rastrea todas las solicitudes en el servicio de Analytics:

**Eventos rastreados:**

- Tipo de servicio (llm_chat, text_to_image, text_to_speech)
- Estado (success, error)
- User ID (si está autenticado)
- Timestamp
- Metadata (response_time, error_message)

## 🐳 Despliegue con Docker

### Build

```bash
docker build -t gateway-api .
```

### Run

```bash
docker run -p 8080:8080 --env-file .env gateway-api
```

### Con Docker Compose

```bash
# Levantar todos los servicios
docker-compose up -d

# Levantar solo el gateway (con sus dependencias)
docker-compose up -d gateway-service

# Ver logs
docker-compose logs -f gateway-service

# Health check
curl http://localhost:8080/health
```

## 🧪 Testing

### Health Check

```bash
curl http://localhost:8080/health
```

Respuesta esperada:

```json
{
  "status": "healthy",
  "service": "api-gateway",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "services": {
    "users": "healthy",
    "llm_chat": "healthy",
    "image": "healthy",
    "speech": "healthy",
    "analytics": "healthy"
  }
}
```

### Ejemplo: Registro de Usuario

```bash
curl -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "securepass123"
  }'
```

### Ejemplo: Chat con LLM

```bash
# Sin autenticación (anónimo)
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?",
    "model": "gpt-4o-mini"
  }'

# Con autenticación
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "message": "Hello, how are you?",
    "model": "gpt-4o-mini",
    "session_id": "optional-session-id"
  }'
```

### Ejemplo: Generar Imagen

```bash
curl -X POST http://localhost:8080/api/image/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "prompt": "A beautiful sunset over mountains",
    "model": "stabilityai/stable-diffusion-3.5-large"
  }'
```

### Ejemplo: Analytics del Usuario

```bash
curl http://localhost:8080/api/analytics/user/me \
  -H "Authorization: Bearer <token>"
```

## 🛠️ Desarrollo

### Instalación Local

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar en modo desarrollo
uvicorn main:app --reload --port 8080
```

### Estructura del Proyecto

```
gateway_api/
├── main.py                 # FastAPI app principal
├── config.py               # Configuración y settings
├── models.py               # Modelos Pydantic
├── auth.py                 # Autenticación JWT
├── service_client.py       # Cliente HTTP para microservicios
├── analytics.py            # Middleware de analytics
├── routes_auth.py          # Rutas de autenticación
├── routes_chat.py          # Rutas de chat
├── routes_image.py         # Rutas de imágenes
├── routes_speech.py        # Rutas de voz
├── routes_analytics.py     # Rutas de analytics
├── requirements.txt        # Dependencias
├── Dockerfile              # Imagen Docker
├── .env                    # Variables de entorno
└── README.md              # Documentación
```

## 🔄 Flujo de Solicitudes

1. **Cliente** → Envía solicitud al Gateway (8080)
2. **Gateway** → Valida autenticación JWT (si requerida)
3. **Gateway** → Proxy la solicitud al microservicio correspondiente
4. **Microservicio** → Procesa la solicitud
5. **Gateway** → Rastrea evento en Analytics (si habilitado)
6. **Gateway** → Retorna respuesta al cliente

## 📝 Logs

El gateway registra:

- Solicitudes entrantes
- Estado de servicios
- Errores y excepciones
- Eventos de analytics

Nivel de logs configurables: DEBUG, INFO, WARNING, ERROR, CRITICAL

## 🚨 Manejo de Errores

El gateway maneja los siguientes tipos de errores:

- **Validación (422)**: Datos de entrada inválidos
- **Autenticación (401)**: Token inválido o expirado
- **Autorización (403)**: Permisos insuficientes
- **Servicio No Disponible (503)**: Microservicio caído
- **Timeout (504)**: Microservicio no responde (>60s)
- **Error Interno (500)**: Errores no manejados

## 🎯 Roadmap

- [ ] Rate limiting por usuario
- [ ] Caché de respuestas
- [ ] Circuit breaker para servicios caídos
- [ ] Métricas con Prometheus
- [ ] Tracing distribuido con OpenTelemetry
- [ ] Logs centralizados con ELK Stack

## 📄 Licencia

MIT
