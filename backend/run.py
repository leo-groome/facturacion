"""
Launcher del servidor — Vanta Facturación
=========================================
En Windows, uvicorn usa ProactorEventLoop por defecto, pero psycopg3
requiere SelectorEventLoop. Este script fija la politica ANTES de que
uvicorn cree el event loop.

Uso (dev):
    python run.py

Equivalente en produccion:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --loop asyncio
"""

import sys
import asyncio

# Fijar SelectorEventLoop en Windows ANTES de que uvicorn arranque
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
