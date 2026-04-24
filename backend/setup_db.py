"""
Script de inicialización de base de datos — Vanta Facturación
=============================================================
Ejecutar una sola vez para crear las tablas en Neon PostgreSQL.

Uso:
    cd backend
    source venv/bin/activate   (o venv\Scripts\activate en Windows)
    python setup_db.py
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

load_dotenv()

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.core.config import get_database_url


DDL = """
CREATE TABLE IF NOT EXISTS clientes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre_empresa VARCHAR(255) NOT NULL,
    rfc VARCHAR(13) UNIQUE NOT NULL,
    contrasena VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS emisores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    rfc VARCHAR(13) NOT NULL,
    regimen_fiscal VARCHAR(10) NOT NULL DEFAULT '626',
    cer_encrypted TEXT,
    key_encrypted TEXT,
    password_encrypted TEXT,
    facturama_synced BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(organization_id, rfc),
    CONSTRAINT chk_regimen_fiscal CHECK (regimen_fiscal ~ '^6\d{2}$')
);

-- Migracion idempotente para instalaciones previas
ALTER TABLE emisores ADD COLUMN IF NOT EXISTS regimen_fiscal VARCHAR(10) NOT NULL DEFAULT '626';

CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    nombre VARCHAR(255) NOT NULL,
    prefix VARCHAR(20) NOT NULL,
    hashed_key TEXT NOT NULL,
    activa BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_emisores_org ON emisores(organization_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_org ON api_keys(organization_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON api_keys(prefix) WHERE activa = TRUE;

CREATE TABLE IF NOT EXISTS facturas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    folio_fiscal UUID,
    facturama_id VARCHAR(100),
    fecha_emision TIMESTAMPTZ,
    receptor_rfc VARCHAR(13) NOT NULL,
    receptor_razon_social VARCHAR(255) NOT NULL,
    receptor_regimen VARCHAR(10),
    receptor_domicilio_fiscal VARCHAR(5),
    receptor_email VARCHAR(255),
    subtotal DECIMAL(15,2) NOT NULL,
    total_impuestos_trasladados DECIMAL(15,2) DEFAULT 0,
    total_impuestos_retenidos DECIMAL(15,2) DEFAULT 0,
    total DECIMAL(15,2) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'Vigente',
    motivo_cancelacion VARCHAR(2),
    folio_sustituto UUID,
    fecha_cancelacion TIMESTAMPTZ,
    xml_content TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chk_estado CHECK (estado IN ('Vigente', 'Cancelado')),
    CONSTRAINT chk_motivo CHECK (motivo_cancelacion IN ('01','02','03','04') OR motivo_cancelacion IS NULL)
);

CREATE INDEX IF NOT EXISTS idx_facturas_org ON facturas(organization_id);
CREATE INDEX IF NOT EXISTS idx_facturas_org_estado ON facturas(organization_id, estado);
CREATE INDEX IF NOT EXISTS idx_facturas_folio ON facturas(folio_fiscal);
"""
# Nota: si clientes ya existe con id INTEGER (de una instalacion anterior),
# eliminala primero con: DROP TABLE clientes CASCADE;  (solo si esta vacia)


async def main():
    import psycopg

    db_url = get_database_url()
    print("Conectando a Neon PostgreSQL...")

    async with await psycopg.AsyncConnection.connect(db_url) as conn:
        async with conn.cursor() as cur:
            await cur.execute(DDL)
            await conn.commit()

    print("Tablas creadas (o ya existian):")
    print("  clientes, emisores, api_keys, facturas")
    print("Setup completado.")


if __name__ == "__main__":
    asyncio.run(main())
