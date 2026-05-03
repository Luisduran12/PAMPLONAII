import httpx
import logging
import re
from typing import List

logger = logging.getLogger(__name__)

class NewsService:
    """Servicio para extraer noticias recientes de la Unipamplona."""
    
    def __init__(self):
        self.url = "https://www.unipamplona.edu.co/"
        self.latest_news = ""

    async def fetch_latest_news(self) -> str:
        """Conecta a la web y extrae titulares."""
        logger.info("Actualizando noticias desde la web oficial...")
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(self.url)
                response.raise_for_status()
                html = response.text
                
                # Extraemos fragmentos de texto que parecen noticias (etiquetas h2, h3 o clases comunes)
                # Buscamos patrones comunes en portales universitarios
                matches = re.findall(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', html)
                
                news_items = []
                # Filtramos para intentar quedarnos solo con lo que parezca una noticia real
                for link, text in matches:
                    text = re.sub(r'<[^>]+>', '', text).strip() # Limpiar HTML
                    if len(text) > 20 and ("noticia" in link.lower() or "/post/" in link.lower() or "evento" in link.lower()):
                        news_items.append(f"- {text}")
                
                if not news_items:
                    # Fallback: Extraer todos los h2/h3 que suelen ser titulares
                    titles = re.findall(r'<(?:h2|h3)[^>]*>(.*?)</(?:h2|h3)>', html)
                    for t in titles:
                        clean_t = re.sub(r'<[^>]+>', '', t).strip()
                        if len(clean_t) > 15:
                            news_items.append(f"- {clean_t}")

                # Guardamos los primeros 10 titulares
                self.latest_news = "\n".join(news_items[:10])
                logger.info("Noticias actualizadas con éxito.")
                return self.latest_news

        except Exception as e:
            logger.error(f"Error cargando noticias de la web: {e}")
            return "No se pudieron cargar las noticias recientes en este momento."

news_service = NewsService()
