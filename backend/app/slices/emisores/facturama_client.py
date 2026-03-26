import httpx
import base64
import os
from typing import Dict, Any

class FacturamaClient:
    """
    Cliente asíncrono básico para interactuar con la API Multiemisor de Facturama.
    """
    def __init__(self):
        self.base_url = os.getenv("FACTURAMA_API_URL", "https://apisandbox.facturama.mx")
        self.user = os.getenv("FACTURAMA_USER", "")
        self.password = os.getenv("FACTURAMA_PASSWORD", "")
        
        credentials = f"{self.user}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        self.headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json"
        }
        
    async def upload_csd(self, rfc: str, cer_base64: str, key_base64: str, password: str) -> Dict[str, Any]:
        """
        Envía los certificados al endpoint de CSD de Facturama de forma asíncrona.
        """
        payload = {
            "Rfc": rfc,
            "Certificate": cer_base64,
            "PrivateKey": key_base64,
            "PrivateKeyPassword": password
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{self.base_url}/csd", 
                json=payload, 
                headers=self.headers
            )
            # Manejamos errores según documentación
            if response.status_code not in (200, 201):
                raise Exception(f"Facturama CSD Error [{response.status_code}]: {response.text}")
            
            return {"status": "success", "rfc": rfc, "details": response.json() if response.text else "ok"}
