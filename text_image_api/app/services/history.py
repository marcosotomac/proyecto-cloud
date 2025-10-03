import json
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.services.s3 import S3Client
from app.services.pollinations import PollinationsClient
from app.models.image import ImageRecord


class ImageHistoryService:
    def __init__(self):
        self.s3_client = S3Client()
        self.pollinations_client = PollinationsClient()

    async def save_image_history(
        self,
        user_id: str,
        username: str,
        prompt: str,
        image_bytes: bytes,
        metadata: Dict[str, Any],
        latency_ms: int
    ) -> Dict[str, Any]:
        """
        Guarda el historial de generación de imagen en S3
        siguiendo la estructura definida en la especificación
        """
        req_id = str(uuid.uuid4())
        dt = datetime.utcnow()
        yyyy, mm, dd = dt.strftime("%Y"), dt.strftime("%m"), dt.strftime("%d")

        # Estructura de carpetas: requests/{yyyy}/{mm}/{dd}/{id}/
        base_path = f"requests/{yyyy}/{mm}/{dd}/{req_id}/"
        print(f"🗂️ Guardando historial en: {base_path}")

        # 1. Guardar input.json
        input_data = {
            "prompt": prompt,
            "size": metadata.get("size", "1024x1024"),
            "seed": metadata.get("seed"),
            "model": metadata.get("model", "flux")
        }
        input_key = base_path + "input.json"
        self.s3_client.put_json(input_key, input_data)

        # 2. Guardar imagen original
        image_key = base_path + "image/original.png"
        self.s3_client.put_bytes(
            image_key,
            image_bytes,
            metadata.get("content_type", "image/png")
        )

        # 3. Crear hash del prompt para privacidad
        prompt_hash = f"sha256:{hashlib.sha256(prompt.encode()).hexdigest()}"

        # 4. Crear record.json
        record_data = {
            "id": req_id,
            "userId": user_id,
            "username": username,
            "service": "image",
            "provider": metadata.get("provider", "pollinations"),
            "model": metadata.get("model", "flux"),
            "prompt": prompt,  # En producción podría ser solo el hash
            "promptHash": prompt_hash,
            "status": 200,
            "latencyMs": latency_ms,
            "tokens": {"in": 0, "out": 0},  # No aplica para imágenes
            "size": {
                "inputBytes": len(prompt.encode()),
                "outputBytes": len(image_bytes)
            },
            "cost": {"usd": 0.0},  # Pollinations es gratuito
            "createdAt": dt.isoformat() + "Z",
            "artifacts": {
                "image": image_key
            },
            "meta": {
                "params": {
                    "size": metadata.get("size", "1024x1024"),
                    "seed": metadata.get("seed"),
                    "model": metadata.get("model", "flux")
                }
            }
        }

        record_key = base_path + "record.json"
        self.s3_client.put_json(record_key, record_data)

        # 5. Actualizar índice por usuario (opcional para listados rápidos)
        await self._update_user_index(user_id, req_id, record_key, yyyy, mm, dd)

        # 6. Retornar respuesta según especificación
        return {
            "id": req_id,
            "s3": {
                "record": record_key,
                "image": image_key
            }
        }

    async def _update_user_index(
        self,
        user_id: str,
        req_id: str,
        record_key: str,
        yyyy: str,
        mm: str,
        dd: str
    ):
        """Actualiza el índice jsonl por usuario para listados rápidos"""
        index_key = f"users/{user_id}/image/history/{yyyy}/{mm}/{dd}.jsonl"

        # Leer índice existente
        existing_data = self.s3_client.try_get_object(index_key)
        existing_content = existing_data.decode() if existing_data else ""

        # Agregar nueva línea
        new_line = json.dumps({
            "id": req_id,
            "record": record_key,
            "timestamp": f"{yyyy}-{mm}-{dd}"
        }) + "\n"

        # Guardar índice actualizado
        updated_content = existing_content + new_line
        self.s3_client.put_bytes(
            index_key,
            updated_content.encode(),
            "application/jsonl"
        )

    async def get_image_record(self, image_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el record de una imagen por su ID"""
        # Búsqueda simple: intentar encontrar en estructura de fechas recientes
        dt = datetime.utcnow()

        # Buscar en los últimos 7 días
        for days_back in range(7):
            search_date = dt - timedelta(days=days_back)
            yyyy, mm, dd = search_date.strftime("%Y"), search_date.strftime(
                "%m"), search_date.strftime("%d")

            record_key = f"requests/{yyyy}/{mm}/{dd}/{image_id}/record.json"

            try:
                record_data = self.s3_client.get_json(record_key)
                return record_data
            except:
                continue

        return None
