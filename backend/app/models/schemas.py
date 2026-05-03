"""
schemas.py
==========
Define los modelos Pydantic usados para validar las peticiones (request)
y respuestas (response) de la API. Pydantic se encarga de la validación
automática y de generar la documentación interactiva (Swagger).
"""

from typing import List, Optional, Literal      # Tipos para anotaciones
from pydantic import BaseModel, Field           # Base para modelos validados
from datetime import datetime                   # Para timestamps


# =====================================================================
# CHAT
# =====================================================================
class ChatMessage(BaseModel):
    """Un mensaje individual dentro de una conversación."""

    # 'user' = pregunta del estudiante, 'assistant' = respuesta de la IA
    role: Literal["user", "assistant"] = Field(
        ..., description="Quién emitió el mensaje"
    )
    # Texto del mensaje
    content: str = Field(..., description="Contenido del mensaje")


class ChatRequest(BaseModel):
    """Lo que envía el frontend cuando el usuario hace una pregunta."""

    # Pregunta actual del usuario (obligatoria, mínimo 1 carácter)
    message: str = Field(..., min_length=1, max_length=2000)

    # Historial previo opcional. Permite mantener contexto entre turnos
    history: Optional[List[ChatMessage]] = Field(
        default_factory=list, description="Historial de la conversación"
    )


class ChatResponse(BaseModel):
    """Respuesta que devuelve el backend al frontend."""

    # Texto que se muestra al usuario
    answer: str

    # De dónde salió la respuesta: "faq" (base de conocimiento) o "ai" (Groq)
    source: Literal["faq", "ai", "fallback"]

    # Si vino de FAQ, devolvemos la pregunta original que coincidió
    matched_question: Optional[str] = None

    # Score de similitud (0.0 a 1.0) cuando viene de FAQ
    confidence: Optional[float] = None


# =====================================================================
# FAQ
# =====================================================================
class FAQItem(BaseModel):
    """Una entrada FAQ tal como se devuelve al frontend."""

    pregunta: str
    respuesta: str
    categoria: Optional[str] = None


# =====================================================================
# FEEDBACK
# =====================================================================
class FeedbackRequest(BaseModel):
    """Datos que envía el frontend al dar like/dislike a una respuesta."""

    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)

    # El frontend envía 1 (útil) o 0 (no útil)
    rating: int = Field(..., ge=0, le=1)

    # Fuente o comentario opcional
    comment: Optional[str] = None
    source: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Confirmación de que el feedback se guardó."""

    status: str = "ok"
    saved_at: datetime
