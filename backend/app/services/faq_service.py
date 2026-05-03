"""
faq_service.py
==============
Servicio que carga las FAQs en memoria al iniciar y permite buscar
la pregunta más similar a la del usuario usando difflib (librería
estándar, sin dependencias extra).

¿Por qué difflib y no embeddings?
    - Cero dependencias adicionales (no requiere modelos descargados)
    - Suficiente para FAQs cortas y bien redactadas
    - Latencia menor a 5ms para 100 FAQs

Si en el futuro necesitas búsqueda semántica más potente, considera
sentence-transformers o usar la API de embeddings de OpenAI/Groq.
"""

import logging                                  # Logs
import re                                       # Normalización de texto
import unicodedata                              # Eliminación de acentos
from difflib import SequenceMatcher             # Similitud entre strings
from functools import lru_cache                 # Caché en memoria
from typing import List, Dict, Optional, Tuple  # Tipos

from app.core.config import settings            # Configuración global
from app.utils.file_reader import read_faq_csv  # Lector del CSV

logger = logging.getLogger(__name__)


class FAQService:
    """Encapsula la carga y búsqueda de FAQs."""

    def __init__(self) -> None:
        # Lista de dicts {pregunta, respuesta, categoria}
        self._faqs: List[Dict[str, str]] = []
        # Versiones normalizadas pre-calculadas para acelerar la búsqueda
        self._normalized_questions: List[str] = []
        # Cargamos al instanciar
        self.reload()

    # ---------------------------------------------------------------
    # Carga / recarga del archivo
    # ---------------------------------------------------------------
    def reload(self) -> None:
        """Lee el CSV y reinicia los índices internos."""
        self._faqs = read_faq_csv(settings.FAQ_CSV)
        self._normalized_questions = [
            self._normalize(faq["pregunta"]) for faq in self._faqs
        ]
        # Limpiamos el caché porque las preguntas pueden haber cambiado
        self.search.cache_clear()
        logger.info("FAQService cargado con %d preguntas", len(self._faqs))

    # ---------------------------------------------------------------
    # Helpers de normalización
    # ---------------------------------------------------------------
    @staticmethod
    def _normalize(text: str) -> str:
        """
        Convierte el texto a una forma canónica para comparar:
            - minúsculas
            - sin tildes/diéresis
            - sin signos de puntuación
            - espacios colapsados
        """
        # Pasamos a minúsculas
        text = text.lower()
        # Descomponemos caracteres acentuados y quitamos los acentos
        text = unicodedata.normalize("NFD", text)
        text = "".join(c for c in text if unicodedata.category(c) != "Mn")
        # Eliminamos signos de puntuación dejando solo letras, números y espacios
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        # Colapsamos múltiples espacios
        text = re.sub(r"\s+", " ", text).strip()
        return text

    # ---------------------------------------------------------------
    # Búsqueda
    # ---------------------------------------------------------------
    @lru_cache(maxsize=256)
    def search(self, query: str) -> Optional[Tuple[Dict[str, str], float]]:
        """
        Busca la FAQ más similar a `query`.

        Devuelve:
            (faq_dict, score) si hay coincidencia por encima del umbral
            None              si ninguna FAQ supera el umbral

        El @lru_cache evita recomputar para preguntas repetidas (cache hit
        es ~1000x más rápido que recalcular).
        """
        # Si no hay FAQs cargadas, no hay nada que buscar
        if not self._faqs:
            return None

        # Normalizamos la consulta del usuario
        normalized_query = self._normalize(query)
        if not normalized_query:
            return None

        # Buscamos la mejor coincidencia
        best_score = 0.0
        best_index = -1

        for i, normalized_q in enumerate(self._normalized_questions):
            # SequenceMatcher devuelve un ratio entre 0.0 y 1.0
            # Es una medida de cuántos caracteres coinciden en orden
            score = SequenceMatcher(None, normalized_query, normalized_q).ratio()

            # Bonus si todas las palabras de la query aparecen en la FAQ
            # Esto ayuda con preguntas reformuladas
            query_words = set(normalized_query.split())
            faq_words = set(normalized_q.split())
            if query_words and query_words.issubset(faq_words):
                score = min(1.0, score + 0.15)

            if score > best_score:
                best_score = score
                best_index = i

        # Solo devolvemos si supera el umbral configurado
        if best_score >= settings.FAQ_SIMILARITY_THRESHOLD and best_index >= 0:
            logger.info(
                "FAQ match: '%s' -> '%s' (score=%.2f)",
                query, self._faqs[best_index]["pregunta"], best_score,
            )
            return self._faqs[best_index], best_score

        logger.info("Sin match FAQ para '%s' (mejor score=%.2f)", query, best_score)
        return None

    # ---------------------------------------------------------------
    # Listado público
    # ---------------------------------------------------------------
    def list_all(self) -> List[Dict[str, str]]:
        """Devuelve todas las FAQs (para el endpoint GET /api/faqs)."""
        return list(self._faqs)


# Instancia única que comparten todos los routers
faq_service = FAQService()
