"""
web_search_service.py
=====================
Raspa páginas oficiales de la Universidad de Pamplona para obtener
información en tiempo real sobre inscripciones, calendario académico,
y otros temas clave.

- No toca ningún otro servicio existente.
- Usa caché de 30 minutos por URL para no sobrecargar la web.
- Falla silenciosamente: si no puede conectar, devuelve cadena vacía.
"""

import httpx
import logging
import re
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# ── Mapa: palabras clave → URLs oficiales de la Unipamplona ─────────────
TOPIC_URLS: Dict[str, list[str]] = {
    "inscripcion": [
        "https://www.unipamplona.edu.co/unipamplona/portalIG/home_1/recursos/01general/home/03052016/home.jsp",
        "https://www.unipamplona.edu.co/",
    ],
    "carrera": [
        "https://www.unipamplona.edu.co/unipamplona/portalIG/home_1/recursos/01general/home/programas.jsp",
        "https://www.unipamplona.edu.co/",
    ],
    "programa": [
        "https://www.unipamplona.edu.co/unipamplona/portalIG/home_1/recursos/01general/home/programas.jsp",
        "https://www.unipamplona.edu.co/",
    ],
    "facultad": [
        "https://www.unipamplona.edu.co/unipamplona/portalIG/home_1/recursos/01general/home/programas.jsp",
        "https://www.unipamplona.edu.co/",
    ],
    "ingenieria": [
        "https://www.unipamplona.edu.co/unipamplona/portalIG/home_1/recursos/01general/home/programas.jsp",
        "https://www.unipamplona.edu.co/",
    ],
    "calendario": [
        "https://www.unipamplona.edu.co/",
    ],
    "noticia": [
        "https://www.unipamplona.edu.co/",
    ],
    "admision": [
        "https://www.unipamplona.edu.co/unipamplona/portalIG/home_1/recursos/01general/home/03052016/home.jsp",
        "https://www.unipamplona.edu.co/",
    ],
    "matricula": [
        "https://www.unipamplona.edu.co/",
    ],
    "semestre": [
        "https://www.unipamplona.edu.co/",
    ],
    "fecha": [
        "https://www.unipamplona.edu.co/",
    ],
    "default": [
        "https://www.unipamplona.edu.co/",
    ],
}

# Tiempo de caché en segundos (30 minutos)
CACHE_TTL = 1800

class WebSearchService:
    """Raspa páginas web oficiales de la Unipamplona y extrae texto relevante."""

    def __init__(self):
        # Caché: url → (timestamp, texto_extraido)
        self._cache: Dict[str, tuple[float, str]] = {}

    def _get_keywords(self, query: str) -> list[str]:
        """Determina qué temas buscar según las palabras de la consulta."""
        q = query.lower()
        matched = []
        for topic in TOPIC_URLS:
            if topic in q:
                matched.append(topic)
        return matched if matched else ["default"]

    async def _fetch_page(self, url: str) -> str:
        """Descarga una URL con caché de 30 minutos."""
        now = time.time()
        if url in self._cache:
            ts, text = self._cache[url]
            if now - ts < CACHE_TTL:
                logger.debug("Web cache hit: %s", url)
                return text

        try:
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                response = await client.get(url, headers={
                    "User-Agent": "PamplonAI-Bot/1.0 (academic assistant)"
                })
                if response.status_code != 200:
                    return ""
                html = response.text
                text = self._extract_text(html)
                self._cache[url] = (now, text)
                logger.info("Web scraped: %s (%d chars)", url, len(text))
                return text
        except Exception as exc:
            logger.warning("No se pudo acceder a %s: %s", url, exc)
            return ""

    @staticmethod
    def _extract_text(html: str) -> str:
        """Extrae texto limpio de un HTML."""
        # Eliminar scripts, estilos y comentarios
        html = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.S | re.I)
        html = re.sub(r'<style[^>]*>.*?</style>',  ' ', html, flags=re.S | re.I)
        html = re.sub(r'<!--.*?-->',               ' ', html, flags=re.S)

        # Extraer encabezados con más relevancia
        headings = re.findall(r'<h[1-4][^>]*>(.*?)</h[1-4]>', html, re.S | re.I)
        heading_text = ' | '.join(
            re.sub(r'<[^>]+>', '', h).strip()
            for h in headings if len(re.sub(r'<[^>]+>', '', h).strip()) > 10
        )

        # Extraer párrafos
        paras = re.findall(r'<p[^>]*>(.*?)</p>', html, re.S | re.I)
        para_text = ' '.join(
            re.sub(r'<[^>]+>', '', p).strip()
            for p in paras if len(re.sub(r'<[^>]+>', '', p).strip()) > 30
        )

        # Combinar y limpiar espacios
        combined = f"{heading_text}\n\n{para_text}"
        combined = re.sub(r'\s{2,}', ' ', combined).strip()
        return combined[:4000]  # Limitamos a 4000 chars para no inflar el prompt

    async def get_context_for_query(self, query: str) -> str:
        """
        Punto de entrada principal.
        Devuelve texto contextual extraído de las páginas oficiales
        relevantes para la consulta. Devuelve '' si falla todo.
        """
        keywords = self._get_keywords(query)
        seen_urls: set[str] = set()
        all_text: list[str] = []

        for kw in keywords:
            urls = TOPIC_URLS.get(kw, TOPIC_URLS["default"])
            for url in urls:
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                text = await self._fetch_page(url)
                if text:
                    all_text.append(f"[Fuente: {url}]\n{text}")

        return "\n\n".join(all_text)


web_search_service = WebSearchService()
