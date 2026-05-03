import logging
from typing import List, Dict, Optional

from app.services.faq_service import faq_service
from app.services.groq_service import groq_service
from app.utils.file_reader import read_pdf_text, read_calendar_xlsx
from app.core.config import settings
from app.services.news_service import news_service
from app.services.web_search_service import web_search_service

logger = logging.getLogger(__name__)

class AIService:
    """Coordinador entre FAQ, Groq y Noticias de la web."""

    def __init__(self) -> None:
        # Pre-cargamos reglamento y calendario al iniciar
        self._reglamento_text = read_pdf_text(settings.REGLAMENTO_PDF)
        self._calendario = read_calendar_xlsx(settings.CALENDARIO_XLSX)
        logger.info("AIService inicializado")

    def reload_knowledge(self) -> None:
        """Recarga el reglamento, calendario y fuerza actualización de noticias."""
        self._reglamento_text = read_pdf_text(settings.REGLAMENTO_PDF)
        self._calendario = read_calendar_xlsx(settings.CALENDARIO_XLSX)
        news_service.latest_news = "" # Forzar recarga en el siguiente uso
        faq_service.reload()
        logger.info("Conocimiento recargado")

    def _build_context(self, query: str) -> str:
        """Búsqueda de contexto inteligente (RAG simplificado)."""
        chunks: List[str] = []
        query_lower = query.lower()
        words = [w.lower() for w in query.split() if len(w) > 3]

        # ---- NOTICIAS RECIENTES ----
        if any(kw in query_lower for kw in ["noticia", "ultimo", "novedad", "evento", "paso en"]):
            if news_service.latest_news:
                chunks.append(f"NOTICIAS RECIENTES DE LA WEB OFICIAL:\n{news_service.latest_news}")

        # ---- RAG REGLAMENTO (Búsqueda por párrafos) ----
        if self._reglamento_text:
            paragraphs = self._reglamento_text.split("\n\n")
            relevant = [p.strip() for p in paragraphs if any(word in p.lower() for word in words)]
            if relevant:
                chunks.append(f"FRAGMENTOS DEL REGLAMENTO:\n{'\n---\n'.join(relevant[:3])}")
            else:
                chunks.append(f"REGLAMENTO (extracto):\n{self._reglamento_text[:800]}")

        # ---- CALENDARIO ----
        if self._calendario:
            relevant_rows = [str(r) for r in self._calendario if any(w in str(r).lower() for w in words)]
            if relevant_rows:
                chunks.append("EVENTOS CALENDARIO:\n" + "\n".join(relevant_rows[:5]))

        return "\n\n".join(chunks)

    async def get_answer_stream(self, message: str, history: Optional[List[Dict[str, str]]] = None):
        """Generador asíncrono que alimenta el streaming."""
        # NOTA: News y web scraping desactivados en producción (Render Free Tier).
        # Causan timeouts al intentar hacer scraping de páginas web externas.
        # El conocimiento académico está integrado en el system prompt de Groq.

        # 2. Contexto local (reglamento + calendario)
        context = self._build_context(message)

        async for chunk in groq_service.generate_response(
            user_message=message,
            history=history or [],
            extra_context=context,
        ):
            yield chunk


# Instancia única
ai_service = AIService()
