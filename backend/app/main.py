"""
main.py
=======
Punto de entrada de la aplicación FastAPI.

Para ejecutar:
    cd backend
    uvicorn app.main:app --reload

La documentación interactiva queda en:
    http://localhost:8000/docs        (Swagger UI)
    http://localhost:8000/redoc       (ReDoc)
"""

import logging                                          # Logs estándar
from pathlib import Path                                # Manejo de rutas
from contextlib import asynccontextmanager              # Lifespan moderno

from fastapi import FastAPI, Request                    # Framework principal
from fastapi.middleware.cors import CORSMiddleware      # Permite llamadas desde el front
from fastapi.responses import JSONResponse              # Respuestas JSON personalizadas
from fastapi.staticfiles import StaticFiles             # Servir el frontend estático

from app.core.config import settings                    # Configuración global
from app.routers import chat as chat_router             # Router con los endpoints


# =====================================================================
# Configuración de logging (debe hacerse antes de instanciar la app)
# =====================================================================
# Nivel DEBUG si DEBUG=True, INFO en producción
log_level = logging.DEBUG if settings.DEBUG else logging.INFO

logging.basicConfig(
    level=log_level,
    # Formato: 2025-01-15 10:30:00 [INFO] app.routers.chat: mensaje
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


# =====================================================================
# Lifespan: código que se ejecuta al arrancar y al apagar el servidor
# =====================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Hooks de arranque y apagado."""
    # ---------- Arranque ----------
    logger.info("=" * 60)
    logger.info("Iniciando %s (DEBUG=%s)", settings.APP_NAME, settings.DEBUG)
    logger.info("Modelo IA: %s", settings.GROQ_MODEL)
    logger.info("=" * 60)
    yield
    # ---------- Apagado ----------
    logger.info("Apagando %s. Hasta pronto.", settings.APP_NAME)


# =====================================================================
# Instancia de la app
# =====================================================================
app = FastAPI(
    title=settings.APP_NAME,
    description="Asistente académico inteligente para preguntas frecuentes",
    version="1.0.0",
    lifespan=lifespan,
)


# =====================================================================
# CORS UNIVERSAL (Solución definitiva para Vercel)
# =====================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================================
# Manejador global de excepciones no capturadas
# =====================================================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Cualquier error no atrapado se loguea y devuelve un 500 limpio."""
    logger.exception("Error no manejado en %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor."},
    )


# =====================================================================
# Endpoints "raíz"
# =====================================================================
@app.get("/api/health")
async def health_check():
    """Endpoint de salud para monitoreo. Devuelve 200 si la app está viva."""
    key = settings.GROQ_API_KEY or ""
    key_status = "NO CONFIGURADA"
    key_hint = ""
    if key and key != "TU_API_KEY_AQUI":
        key_status = "CONFIGURADA"
        key_hint = f"{key[:8]}...{key[-4:]}"
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "model": settings.GROQ_MODEL,
        "groq_key": key_status,
        "key_hint": key_hint,
    }


# Registramos el router con todos los endpoints /api/*
app.include_router(chat_router.router)


# Servir el frontend estático (HTML/CSS/JS)
# Ahora el frontend vive en la raíz del repositorio para compatibilidad con Vercel.
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent

if FRONTEND_DIR.exists():
    # html=True hace que / sirva index.html automáticamente
    app.mount(
        "/",
        StaticFiles(directory=FRONTEND_DIR, html=True),
        name="frontend",
    )
    logger.info("Frontend servido desde %s", FRONTEND_DIR)
else:
    logger.warning("Carpeta frontend no encontrada en %s", FRONTEND_DIR)
