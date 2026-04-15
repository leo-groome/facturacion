import base64
import os
from typing import Any, Dict, Optional

import httpx


# Tipos MIME para descarga de CFDI
_CONTENT_TYPES = {
    "xml": "application/xml",
    "pdf": "application/pdf",
    "zip": "application/zip",
}


class FacturamaClient:
    """
    Cliente asíncrono para la API Multiemisor de Facturama.
    Cubre el ciclo completo: CSD → Emitir → Descargar → Cancelar.
    """

    def __init__(self):
        self.base_url = os.getenv("FACTURAMA_API_URL", "https://apisandbox.facturama.mx")
        user = os.getenv("FACTURAMA_USER", "")
        password = os.getenv("FACTURAMA_PASSWORD", "")

        encoded_credentials = base64.b64encode(f"{user}:{password}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # CSD
    # ------------------------------------------------------------------

    async def upload_csd(self, rfc: str, cer_base64: str, key_base64: str, password: str) -> Dict[str, Any]:
        """POST /csd — Registra el Certificado de Sello Digital del emisor."""
        payload = {
            "Rfc": rfc,
            "Certificate": cer_base64,
            "PrivateKey": key_base64,
            "PrivateKeyPassword": password,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{self.base_url}/csd",
                json=payload,
                headers=self.headers,
            )
            if response.status_code not in (200, 201):
                raise Exception(f"Facturama CSD Error [{response.status_code}]: {response.text}")
            return {"status": "success", "rfc": rfc, "details": response.json() if response.text else "ok"}

    # ------------------------------------------------------------------
    # CFDI 4.0 — Emisión
    # ------------------------------------------------------------------

    async def issue_cfdi(self, payload: dict) -> Dict[str, Any]:
        """
        POST /cfdi40 — Timbra un CFDI 4.0.
        Retorna dict con al menos: Id (facturama_id), FolioFiscal, Date, Total, Xml (base64).
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/cfdi40",
                json=payload,
                headers=self.headers,
            )
            if response.status_code not in (200, 201):
                raise Exception(f"Facturama Issue Error [{response.status_code}]: {response.text}")
            return response.json()

    # ------------------------------------------------------------------
    # CFDI 4.0 — Descarga
    # ------------------------------------------------------------------

    async def get_cfdi(self, facturama_id: str) -> Dict[str, Any]:
        """GET /cfdi40/issued/{id} — Metadatos del CFDI timbrado."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{self.base_url}/cfdi40/issued/{facturama_id}",
                headers=self.headers,
            )
            if response.status_code != 200:
                raise Exception(f"Facturama Get Error [{response.status_code}]: {response.text}")
            return response.json()

    async def download_cfdi(self, facturama_id: str, formato: str) -> bytes:
        """
        GET /cfdi40/issued/{id}/{formato} — Descarga XML, PDF o ZIP.
        Facturama devuelve el contenido en base64 dentro de un JSON: {"Content": "<base64>"}
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/cfdi40/issued/{facturama_id}/{formato}",
                headers=self.headers,
            )
            if response.status_code != 200:
                raise Exception(f"Facturama Download Error [{response.status_code}]: {response.text}")

            data = response.json()
            # Facturama devuelve: {"Content": "<base64>", "ContentType": "...", "FileName": "..."}
            content_b64 = data.get("Content") or data.get("content") or ""
            return base64.b64decode(content_b64)

    # ------------------------------------------------------------------
    # CFDI 4.0 — Cancelación
    # ------------------------------------------------------------------

    async def cancel_cfdi(
        self,
        facturama_id: str,
        motivo: str,
        folio_sustituto: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        DELETE /cfdi40/issued/{id}?motive={motivo}&uuidReplacement={folio}
        Motivos SAT: 01=Comprobante emitido con errores con relacion,
                     02=Comprobante emitido con errores sin relacion,
                     03=No se llevo a cabo la operacion,
                     04=Operacion nominativa relacionada en la factura global.
        """
        params: Dict[str, str] = {"motive": motivo}
        if folio_sustituto:
            params["uuidReplacement"] = folio_sustituto

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{self.base_url}/cfdi40/issued/{facturama_id}",
                params=params,
                headers=self.headers,
            )
            if response.status_code not in (200, 202):
                raise Exception(f"Facturama Cancel Error [{response.status_code}]: {response.text}")
            return response.json() if response.text else {"status": "cancelled"}
