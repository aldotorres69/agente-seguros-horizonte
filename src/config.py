"""
Configuración central del Agente de Seguros Horizonte S.A.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

# Fecha de referencia mandatoria según negocio
REFERENCE_DATE = "2026-10-15"

# Rutas de datos y documentos
DATOS_DIR = ROOT_DIR / "datos"
CONDICIONADOS_DIR = ROOT_DIR / "condicionados"
LOGS_DIR = ROOT_DIR / "logs"
CASOS_DIR = ROOT_DIR / "casos_prueba"

# Asegurar existencia de directorio de logs
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configuración del LLM
AI_PROVIDER = os.getenv("AI_PROVIDER", "auto").lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "").strip() or None
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini").strip()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip()
