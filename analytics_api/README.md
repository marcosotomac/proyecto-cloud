# Analytics API

Microservicio de analítica y seguimiento de uso para la plataforma de microservicios LLM.

## 🎯 Funcionalidades

- ✅ Seguimiento de eventos de uso de todos los microservicios
- ✅ Analítica por usuario (autenticados y anónimos)
- ✅ Analítica por servicio (LLM Chat, Text-to-Image, Text-to-Speech)
- ✅ Analítica del sistema completo
- ✅ Estadísticas de uso detalladas por período de tiempo
- ✅ Top usuarios por volumen de uso
- ✅ Métricas de éxito/error por servicio
- ✅ Seguimiento de tokens (LLM)
- ✅ Seguimiento de almacenamiento (S3)
- ✅ Tiempos de respuesta promedio

## 📊 Métricas Recopiladas

### LLM Chat

- Total de conversaciones
- Tokens de entrada/salida
- Modelos utilizados
- Tiempo de respuesta
- Tasa de éxito/error

### Text-to-Image

- Total de imágenes generadas
- Tamaño de prompts
- Tamaño de imágenes en S3
- Tiempo de generación
- Tasa de éxito/error

### Text-to-Speech

- Total de audios generados
- Longitud de texto convertido
- Voces/idiomas utilizados
- Duración de audios
- Tamaño de archivos en S3
- Tasa de éxito/error

## 🔧 Configuración

### Variables de Entorno

```env
NODE_ENV=development
PORT=8005

# MongoDB
MONGO_URI=mongodb://mongo:27017/analytics_db

# JWT
JWT_ACCESS_SECRET=dev-super-secret-access-key-2024

# Services URLs
USERS_SERVICE_URL=http://users-service:3000
LLM_SERVICE_URL=http://llm-chat-service:8002
IMAGE_SERVICE_URL=http://text-image-service:8000
SPEECH_SERVICE_URL=http://text-speech-service:8000

# S3
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=minio
S3_SECRET_KEY=minio123

# Logging
LOG_LEVEL=INFO
```

### Inicio Rápido

```bash
# Desde la raíz del proyecto
docker-compose up --build -d analytics-service

# Ver logs
docker logs -f llm-analytics-service
```

## 📡 Endpoints

### 1. Health Check

```bash
GET /health
```

**Respuesta:**

```json
{
  "status": "healthy",
  "service": "analytics-api",
  "version": "1.0.0",
  "database": "connected"
}
```

### 2. Rastrear Evento (Para Microservicios)

```bash
POST /analytics/track
Content-Type: application/json
Authorization: Bearer <jwt_token>  # Opcional
```

**Body:**

```json
{
  "service_type": "llm_chat",
  "event_type": "success",
  "metadata": {
    "model": "gpt-4o-mini",
    "input_tokens": 150,
    "output_tokens": 300,
    "response_time_ms": 850
  }
}
```

**Respuesta:**

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-10-02T10:30:00Z",
  "message": "Event tracked successfully"
}
```

### 3. Analítica de Usuario

```bash
GET /analytics/user?user_id=123&time_range=week
```

**Query Parameters:**

- `user_id` (opcional): ID del usuario (vacío = usuario actual o anónimo)
- `time_range` (opcional): hour, day, week, month, year, all (default: all)

**Respuesta:**

```json
{
  "user_id": "123",
  "total_requests": 450,
  "successful_requests": 425,
  "failed_requests": 25,
  "success_rate": 94.44,
  "llm_chat_requests": 200,
  "image_generation_requests": 150,
  "speech_generation_requests": 100,
  "total_input_tokens": 45000,
  "total_output_tokens": 67000,
  "total_tokens": 112000,
  "total_storage_bytes": 5242880,
  "avg_response_time_ms": 1250.5,
  "first_request": "2025-09-25T10:00:00Z",
  "last_request": "2025-10-02T15:30:00Z"
}
```

### 4. Mi Analítica (Usuario Autenticado)

```bash
GET /analytics/user/me?time_range=month
Authorization: Bearer <jwt_token>
```

**Respuesta:** Misma estructura que `/analytics/user`

### 5. Analítica por Servicio

```bash
GET /analytics/service/llm_chat?time_range=week
```

**Servicios Disponibles:**

- `llm_chat`
- `text_to_image`
- `text_to_speech`

**Respuesta:**

```json
{
  "service_type": "llm_chat",
  "total_requests": 5000,
  "successful_requests": 4750,
  "failed_requests": 250,
  "success_rate": 95.0,
  "unique_users": 150,
  "anonymous_users": 50,
  "avg_response_time_ms": 1150.5,
  "service_metrics": {}
}
```

### 6. Analítica del Sistema

```bash
GET /analytics/system?time_range=month&top_users_limit=10
```

**Respuesta:**

```json
{
  "total_requests": 15000,
  "total_users": 250,
  "total_anonymous_requests": 3000,
  "services": [
    {
      "service_type": "llm_chat",
      "total_requests": 6000,
      "unique_users": 200,
      "success_rate": 95.5
    },
    {
      "service_type": "text_to_image",
      "total_requests": 5000,
      "unique_users": 180,
      "success_rate": 92.0
    },
    {
      "service_type": "text_to_speech",
      "total_requests": 4000,
      "unique_users": 150,
      "success_rate": 97.5
    }
  ],
  "top_users": [
    { "user_id": "user_123", "request_count": 500 },
    { "user_id": "user_456", "request_count": 450 }
  ],
  "start_date": "2025-09-02T00:00:00Z",
  "end_date": "2025-10-02T23:59:59Z"
}
```

### 7. Estadísticas de Uso Detalladas

```bash
GET /analytics/usage?user_id=123&time_range=week
```

**Respuesta:**

```json
{
  "time_range": "week",
  "user_id": "123",
  "requests_by_period": {
    "2025-09-26": 45,
    "2025-09-27": 52,
    "2025-09-28": 38,
    "2025-09-29": 60,
    "2025-09-30": 55,
    "2025-10-01": 48,
    "2025-10-02": 42
  },
  "requests_by_service": {
    "llm_chat": 150,
    "text_to_image": 100,
    "text_to_speech": 90
  },
  "success_rate_by_service": {
    "llm_chat": 96.5,
    "text_to_image": 93.2,
    "text_to_speech": 98.1
  }
}
```

## 🔗 Integración con Microservicios

Los microservicios deben enviar eventos al Analytics API después de procesar solicitudes:

### Ejemplo en LLM Chat Service

```python
import httpx

async def track_llm_event(user_id, model, input_tokens, output_tokens, response_time):
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://analytics-service:8005/analytics/track",
            json={
                "user_id": user_id,
                "service_type": "llm_chat",
                "event_type": "success",
                "metadata": {
                    "model": model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "response_time_ms": response_time
                }
            }
        )
```

### Ejemplo en Text-to-Image Service

```python
async def track_image_event(user_id, prompt_length, image_size_bytes):
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://analytics-service:8005/analytics/track",
            json={
                "user_id": user_id,
                "service_type": "text_to_image",
                "event_type": "success",
                "metadata": {
                    "prompt_length": prompt_length,
                    "size_bytes": image_size_bytes,
                    "image_size": "1024x1024"
                }
            }
        )
```

### Ejemplo en Text-to-Speech Service

```python
async def track_speech_event(user_id, text_length, audio_size_bytes, duration):
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://analytics-service:8005/analytics/track",
            json={
                "user_id": user_id,
                "service_type": "text_to_speech",
                "event_type": "success",
                "metadata": {
                    "text_length": text_length,
                    "size_bytes": audio_size_bytes,
                    "duration_seconds": duration,
                    "voice": "alloy",
                    "language": "en"
                }
            }
        )
```

## 📊 Estructura de Base de Datos

### Colección: analytics_events

```javascript
{
  "_id": ObjectId,
  "event_id": "uuid",
  "user_id": "user_123" | null,
  "service_type": "llm_chat" | "text_to_image" | "text_to_speech",
  "event_type": "request" | "success" | "error" | "generation",
  "timestamp": ISODate,
  "metadata": {
    // Campos específicos del servicio
    "model": "gpt-4o-mini",
    "input_tokens": 150,
    "output_tokens": 300,
    "response_time_ms": 850,
    "size_bytes": 524288,
    ...
  }
}
```

### Índices

- `user_id`
- `service_type`
- `event_type`
- `timestamp`
- `(user_id, timestamp)` - compuesto
- `(service_type, timestamp)` - compuesto

## 🎯 Casos de Uso

### 1. Dashboard de Administrador

```bash
# Ver analítica del sistema completo
curl http://localhost:8005/analytics/system?time_range=month

# Ver top 20 usuarios
curl http://localhost:8005/analytics/system?top_users_limit=20
```

### 2. Panel de Usuario

```bash
# Usuario ve sus propias estadísticas
curl http://localhost:8005/analytics/user/me?time_range=week \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Monitoreo de Servicios

```bash
# Ver rendimiento del servicio LLM
curl http://localhost:8005/analytics/service/llm_chat?time_range=day

# Comparar todos los servicios
for service in llm_chat text_to_image text_to_speech; do
  curl http://localhost:8005/analytics/service/$service?time_range=day
done
```

### 4. Análisis de Tendencias

```bash
# Ver uso semanal detallado
curl http://localhost:8005/analytics/usage?time_range=week

# Ver patrones de un usuario específico
curl http://localhost:8005/analytics/usage?user_id=123&time_range=month
```

## 🔍 Debugging

```bash
# Ver logs
docker logs -f llm-analytics-service

# Verificar salud
curl http://localhost:8005/health

# Probar conexión a MongoDB
docker exec -it llm-mongo mongosh analytics_db --eval "db.analytics_events.countDocuments()"

# Ver últimos eventos
docker exec -it llm-mongo mongosh analytics_db --eval "db.analytics_events.find().sort({timestamp: -1}).limit(5)"
```

## 📈 Métricas Importantes

- **Success Rate**: Porcentaje de solicitudes exitosas vs fallidas
- **Response Time**: Tiempo promedio de respuesta por servicio
- **Token Usage**: Tokens consumidos (importante para costos de LLM)
- **Storage Usage**: Espacio utilizado en S3 por usuario
- **User Activity**: Usuarios activos por período
- **Peak Usage**: Horas/días de mayor uso

## 🚀 Roadmap

- [ ] Agregar alertas cuando métricas excedan umbrales
- [ ] Implementar dashboard web con gráficas
- [ ] Exportar métricas a Prometheus
- [ ] Agregar análisis predictivo de uso
- [ ] Implementar límites de rate por usuario
- [ ] Agregar facturación basada en uso
- [ ] Webhooks para eventos importantes

## 📄 Licencia

MIT
