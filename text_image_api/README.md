# Text-to-Image Microservice

Microservicio para generar imágenes usando [Pollinations.ai](https://pollinations.ai) con almacenamiento de historial en S3/MinIO.

## 🚀 Inicio Rápido

### 1. Desarrollo Local (con Docker)

```bash
# Construir y levantar servicios
docker compose up --build

# Solo levantar (si ya está construido)
docker compose up

# Ver logs
docker compose logs -f text-image-api
```

### 2. Desarrollo Local (sin Docker)

```bash
# Instalar dependencias
pip install -r requirements.txt

# Copiar variables de entorno
cp .env.example .env

# Editar .env para desarrollo local:
# S3_ENDPOINT=http://localhost:9000

# Levantar solo MinIO
docker compose up minio -d

# Ejecutar la aplicación
python main.py
```

## 📡 Endpoints

### Generar Imagen

```bash
POST http://localhost:8000/image/generate
Content-Type: application/json

{
  "prompt": "cyberpunk alpaca with neon lights",
  "size": "1024x1024",
  "seed": 12345,
  "model": "flux"
}
```

**Respuesta:**

```json
{
  "id": "7a1c2e3f-4b5d-6789-abcd-ef0123456789",
  "status": "completed",
  "s3": {
    "record": "requests/2025/10/01/7a1c.../record.json",
    "image": "requests/2025/10/01/7a1c.../image/original.png"
  },
  "meta": {
    "provider": "pollinations",
    "model": "flux",
    "size": "1024x1024",
    "latencyMs": 1420,
    "contentType": "image/png"
  }
}
```

### Obtener Información de Imagen

```bash
GET http://localhost:8000/image/{image_id}
```

### Descargar Imagen (URL firmada)

```bash
GET http://localhost:8000/image/{image_id}/download
```

### Health Check

```bash
GET http://localhost:8000/healthz
```

## 🏗️ Arquitectura

```
[Cliente]
    ↓ HTTP
[FastAPI Service]
    ├── Pollinations.ai (generar imagen)
    ├── MinIO/S3 (guardar historial + imagen)
    └── Analytics (eventos - futuro)
```

## 📁 Estructura de Almacenamiento S3

```
llmhist-image-dev/
├── requests/
│   └── {yyyy}/{mm}/{dd}/{request-id}/
│       ├── input.json      # Parámetros de entrada
│       ├── record.json     # Metadatos completos
│       └── image/
│           └── original.png # Imagen generada
└── users/
    └── {user-id}/image/history/
        └── {yyyy}/{mm}/{dd}.jsonl  # Índice por usuario
```

## 🔧 Configuración

Ver `.env.example` para todas las variables disponibles.

**Variables clave:**

- `S3_ENDPOINT`: URL de MinIO/S3
- `S3_BUCKET`: Bucket para guardar imágenes
- `POLLINATIONS_BASE_URL`: URL base de Pollinations.ai

## 🌐 Acceso a MinIO Web Console

- URL: http://localhost:9001
- Usuario: `minio`
- Contraseña: `minio123`

## 📊 Monitoring

- Health check: `GET /healthz`
- Métricas: `GET /` (info básica del servicio)

## 🔄 Próximos Pasos

1. ✅ Generación básica de imágenes con Pollinations.ai
2. ✅ Almacenamiento de historial en S3/MinIO
3. ⏳ Integración con servicio de Analytics
4. ⏳ Autenticación JWT
5. ⏳ Rate limiting
6. ⏳ Métricas Prometheus
