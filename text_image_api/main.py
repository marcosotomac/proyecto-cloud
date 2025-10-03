from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
import time
import uuid
import sys
import logging
from typing import Optional, Dict, Any
from app.config import settings
from app.models.image import ImageGenerationRequest, ImageGenerationResponse
from app.services.pollinations import PollinationsClient
from app.services.s3 import S3Client
from app.services.history import ImageHistoryService
from app.auth import get_current_user_optional, get_current_user

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear instancia de FastAPI
app = FastAPI(
    title="LLM Text-to-Image Microservice",
    description="Microservicio para generar imágenes usando Pollinations.ai",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instanciar servicios
pollinations_client = PollinationsClient()
s3_client = S3Client()
history_service = ImageHistoryService()


@app.on_event("startup")
async def startup_event():
    """Inicialización del servicio"""
    await s3_client.ensure_bucket_exists()
    print(f"✅ Text-to-Image service started on port {settings.port}")
    print(f"✅ S3 bucket '{settings.s3_bucket}' ready")


@app.get("/")
async def root():
    return {
        "service": "text-to-image",
        "version": "1.0.0",
        "provider": "pollinations",
        "status": "ready"
    }


@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": time.time()}


@app.post("/image/generate", response_model=ImageGenerationResponse)
async def generate_image(
    request: ImageGenerationRequest,
    current_user: Optional[Dict[str, Any]] = Depends(
        get_current_user_optional),
    x_request_id: Optional[str] = Header(None, alias="x-request-id"),
):
    """
    Genera una imagen usando Pollinations.ai

    Siguiendo la especificación:
    - POST /image/generate { prompt, size?, seed?, style? } 
    - → { id, s3:{record,image,preview?}, meta }

    Acepta usuarios autenticados y anónimos.
    """

    # Generar IDs si no se proporcionan
    request_id = x_request_id or str(uuid.uuid4())

    # Obtener información del usuario (autenticado o anónimo)
    logger.info(f"Current user received: {current_user}")
    if current_user:
        user_id = current_user["user_id"]
        username = current_user["email"]
        logger.info(f"Authenticated user: {user_id} ({username})")
    else:
        user_id = "anonymous"
        username = "anonymous"
        logger.info("Anonymous user request")

    start_time = time.time()

    try:
        print(f"🚀 Iniciando generación para prompt: '{request.prompt}'")

        # 1. Generar imagen con Pollinations
        image_bytes, metadata = await pollinations_client.generate_image(
            prompt=request.prompt,
            size=request.size,
            seed=request.seed,
            model=request.model or "flux"
        )

        latency_ms = int((time.time() - start_time) * 1000)
        print(
            f"🖼️ Imagen generada, latencia: {latency_ms}ms, tamaño: {len(image_bytes)} bytes")

        # 2. Guardar historial en S3
        print(f"💾 Guardando historial para usuario: {user_id}")
        result = await history_service.save_image_history(
            user_id=user_id,
            username=username,
            prompt=request.prompt,
            image_bytes=image_bytes,
            metadata=metadata,
            latency_ms=latency_ms
        )
        print(f"✅ Historial guardado: {result['id']}")

        # 3. TODO: Enviar evento a Analytics (cuando esté implementado)
        # await send_analytics_event(...)

        # 4. Preparar respuesta
        response = ImageGenerationResponse(
            id=result["id"],
            status="completed",
            prompt=request.prompt,
            user_id=user_id if user_id != "anonymous" else None,
            s3=result["s3"],
            meta={
                "provider": metadata["provider"],
                "model": metadata["model"],
                "size": metadata["size"],
                "latencyMs": latency_ms,
                "contentType": metadata["content_type"]
            }
        )

        return response

    except Exception as e:
        print(f"❌ Error generating image: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating image: {str(e)}"
        )


@app.get("/image/{image_id}")
async def get_image(image_id: str):
    """
    Obtiene información de una imagen generada por su ID

    Siguiendo la especificación:
    - GET /image/:id → { status, s3Keys, meta }
    """

    try:
        print(f"🔍 Buscando imagen con ID: {image_id}", flush=True)

        # Obtener record de la imagen
        record = await history_service.get_image_record(image_id)

        print(f"📄 Record encontrado: {record is not None}", flush=True)

        if not record:
            print(f"❌ Imagen {image_id} no encontrada")
            raise HTTPException(
                status_code=404,
                detail=f"Image with ID {image_id} not found"
            )

        print(f"✅ Retornando información de imagen {image_id}")
        return {
            "id": image_id,
            "status": "completed",
            "s3Keys": record.get("artifacts", {}),
            "meta": record.get("meta", {})
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error retrieving image {image_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving image: {str(e)}"
        )


@app.get("/image/{image_id}/download")
async def download_image(
    image_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """
    Genera una URL firmada para descargar la imagen
    Accesible para usuarios autenticados y anónimos
    """
    try:
        record = await history_service.get_image_record(image_id)

        if not record:
            raise HTTPException(
                status_code=404,
                detail=f"Image with ID {image_id} not found"
            )

        image_key = record.get("artifacts", {}).get("image")
        if not image_key:
            raise HTTPException(
                status_code=404,
                detail="Image file not found in storage"
            )

        # Generar URL firmada válida por 5 minutos
        signed_url = s3_client.generate_signed_url(image_key, expiration=300)

        return {
            "downloadUrl": signed_url,
            "expiresIn": 300,
            "user": current_user["email"] if current_user else "anonymous"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error generating download URL for {image_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating download URL: {str(e)}"
        )


@app.get("/admin/images")
async def list_images_admin(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Endpoint protegido solo para usuarios autenticados
    Lista las imágenes del usuario actual
    """
    user_id = current_user["user_id"]
    username = current_user["email"]

    # En una implementación real, esto buscaría en S3 o una base de datos
    # Por ahora, retornamos información básica
    return {
        "message": "Protected endpoint accessed successfully",
        "user": {
            "id": user_id,
            "email": username
        },
        "images": []  # Aquí iría la lista real de imágenes
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
