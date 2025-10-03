import httpx
from typing import Optional, Dict, Any
from config import settings
import logging

logger = logging.getLogger(__name__)


class ServiceClient:
    """HTTP client for communicating with microservices"""

    def __init__(self, service_url: str, service_name: str):
        self.service_url = service_url
        self.service_name = service_name
        self.timeout = httpx.Timeout(timeout=60.0, connect=10.0)

    async def request(
        self,
        method: str,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
        """
        Make a request to the service

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint path
            headers: Optional request headers
            json: Optional JSON body
            params: Optional query parameters
            data: Optional form data

        Returns:
            httpx.Response
        """
        url = f"{self.service_url}{endpoint}"

        try:
            logger.info(f"[{self.service_name}] {method} {url}")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json,
                    params=params,
                    data=data
                )

                logger.info(
                    f"[{self.service_name}] Response: {response.status_code}")
                return response

        except httpx.TimeoutException as e:
            logger.error(f"[{self.service_name}] Timeout: {str(e)}")
            raise Exception(f"{self.service_name} service timeout")
        except httpx.ConnectError as e:
            logger.error(f"[{self.service_name}] Connection error: {str(e)}")
            raise Exception(f"{self.service_name} service unavailable")
        except Exception as e:
            logger.error(f"[{self.service_name}] Error: {str(e)}")
            raise


# Service clients instances
users_client = ServiceClient(settings.USERS_SERVICE_URL, "Users")
llm_client = ServiceClient(settings.LLM_SERVICE_URL, "LLM")
image_client = ServiceClient(settings.IMAGE_SERVICE_URL, "Image")
speech_client = ServiceClient(settings.SPEECH_SERVICE_URL, "Speech")
analytics_client = ServiceClient(settings.ANALYTICS_SERVICE_URL, "Analytics")
