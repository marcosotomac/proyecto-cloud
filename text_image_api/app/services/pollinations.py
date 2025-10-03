import httpx
import hashlib
from typing import Optional
from datetime import datetime
from app.config import settings


class PollinationsClient:
    def __init__(self):
        self.base_url = settings.pollinations_base_url

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        seed: Optional[int] = None,
        model: str = "flux"
    ) -> tuple[bytes, dict]:
        """
        Genera una imagen usando Pollinations.ai
        Retorna: (image_bytes, metadata)
        """
        # Construir URL con parámetros
        url = f"{self.base_url}/{prompt}"

        params = {
            "model": model,
            "width": size.split("x")[0],
            "height": size.split("x")[1]
        }

        if seed:
            params["seed"] = seed

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()

            image_bytes = response.content

            metadata = {
                "provider": "pollinations",
                "model": model,
                "size": size,
                "seed": seed,
                "content_type": response.headers.get("content-type", "image/png"),
                "content_length": len(image_bytes)
            }

            return image_bytes, metadata

    def create_prompt_hash(self, prompt: str) -> str:
        """Crea un hash SHA256 del prompt para privacidad"""
        return hashlib.sha256(prompt.encode()).hexdigest()
