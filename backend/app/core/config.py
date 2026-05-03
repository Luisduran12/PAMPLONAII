"""
config.py
=========
Carga las variables de entorno desde .env y las expone como un objeto
de configuración tipado (Settings). Cualquier módulo de la app debe
importar `settings` desde aquí en vez de leer os.environ directamente.

Si necesitas añadir una nueva variable de configuración:
    1. Añádela al archivo .env
    2. Añádela como atributo en la clase Settings
    3. Impórtala desde donde la necesites
"""

import os                                          # Acceso al sistema operativo
from pathlib import Path                           # Manejo moderno de rutas
from dotenv import load_dotenv                     # Carga variables del .env

# -----------------------------------------------------------------
# Localizamos la raíz del backend (dos niveles arriba de este archivo)
# /backend/app/core/config.py -> sube a /backend/app/core -> /backend/app -> /backend
# -----------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Cargamos las variables del archivo .env ubicado en /backend/.env
load_dotenv(BASE_DIR / ".env")


class Settings:
    """Contenedor tipado de toda la configuración de la app."""

    # ------------- Configuración general -------------
    # Nombre de la app (aparece en la documentación de FastAPI)
    APP_NAME: str = os.getenv("APP_NAME", "PamplonAI-V2-Prod")

    # Modo debug: activa logs detallados y CORS abierto a cualquier origen
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # ------------- Configuración de Groq -------------
    # Clave de la API de Groq, obligatoria para que el chat funcione
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # Modelo de Groq a usar (ver https://console.groq.com/docs/models)
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Timeout en segundos para las llamadas HTTP a Groq
    GROQ_TIMEOUT: float = float(os.getenv("GROQ_TIMEOUT", "15"))

    # URL base de la API de Groq (compatible con el formato OpenAI)
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    # ------------- Configuración FAQ -------------
    # Umbral de similitud (0.0 a 1.0) para considerar una FAQ como respuesta válida
    # Si la mejor coincidencia tiene un score menor, se delega a Groq
    FAQ_SIMILARITY_THRESHOLD: float = float(
        os.getenv("FAQ_SIMILARITY_THRESHOLD", "0.55")
    )

    # ------------- Rutas de archivos -------------
    # Carpeta donde están los archivos de conocimiento (CSV, XLSX, PDF)
    DATA_DIR: Path = BASE_DIR / "data"

    # Rutas específicas de cada archivo de conocimiento
    FAQ_CSV: Path = DATA_DIR / "faq.csv"
    CALENDARIO_XLSX: Path = DATA_DIR / "calendario.xlsx"
    REGLAMENTO_PDF: Path = DATA_DIR / "reglamento.pdf"

    # Archivo donde se guardan los feedbacks (se crea solo si no existe)
    FEEDBACK_FILE: Path = DATA_DIR / "feedback.csv"


# Instancia única que se importa en toda la app
settings = Settings()
