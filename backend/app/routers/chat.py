import logging
import json
import csv
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatRequest, FAQItem, FeedbackRequest, FeedbackResponse
from app.services.ai_service import ai_service
from app.services.faq_service import faq_service
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])

@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Endpoint con soporte para Streaming.
    Devuelve un flujo de datos (Server-Sent Events simplificado).
    """
    logger.info("Consulta recibida: %s", request.message[:50])
    
    # Paso 1: Intentar FAQ (coincidencia exacta/similitud alta)
    match = faq_service.search(request.message)
    if match:
        faq, score = match
        # Si es FAQ, devolvemos un JSON directo pero envuelto en una respuesta de una sola vez
        async def single_hit():
            yield json.dumps({
                "answer": faq["respuesta"],
                "source": "faq",
                "matched_question": faq["pregunta"],
                "confidence": round(score, 3)
            })
        return StreamingResponse(single_hit(), media_type="application/json")

    # Paso 2: Si no es FAQ, vamos a la IA con Streaming
    async def ai_streamer():
        history_dicts = [m.model_dump() for m in (request.history or [])]
        
        # Primero enviamos el "header" del mensaje para que el front sepa que es IA
        yield json.dumps({"source": "ai"}) + "||SPLIT||"
        
        # Luego enviamos el contenido según llega de Groq
        async for chunk in ai_service.get_answer_stream(request.message, history_dicts):
            yield chunk

    return StreamingResponse(ai_streamer(), media_type="text/plain")

@router.get("/faqs", response_model=list[FAQItem])
async def list_faqs():
    raw = faq_service.list_all()
    return [FAQItem(**item) for item in raw]

@router.post("/feedback", response_model=FeedbackResponse)
async def save_feedback(feedback: FeedbackRequest):
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    file_exists = settings.FEEDBACK_FILE.exists()
    now = datetime.now()
    try:
        with open(settings.FEEDBACK_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "question", "answer", "rating", "comment"])
            writer.writerow([now.isoformat(), feedback.question, feedback.answer, feedback.rating, feedback.comment or ""])
        return FeedbackResponse(status="ok", saved_at=now)
    except Exception as exc:
        logger.exception("Error feedback: %s", exc)
        raise HTTPException(status_code=500, detail="No se pudo guardar")

@router.post("/reload")
async def reload_knowledge():
    ai_service.reload_knowledge()
    return {"status": "ok"}
