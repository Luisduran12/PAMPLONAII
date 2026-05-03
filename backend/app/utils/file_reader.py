"""
file_reader.py
==============
Funciones utilitarias para leer los archivos de conocimiento.
Centraliza la lógica de I/O para que los servicios solo se preocupen
por la lógica de negocio.

Si quieres soportar un nuevo formato (ej: .docx), añade una función aquí.
"""

import logging                                  # Sistema de logs estándar
from pathlib import Path                        # Manejo de rutas
from typing import List, Dict                   # Tipos para anotaciones

import pandas as pd                             # Para leer CSV y XLSX
from pypdf import PdfReader                     # Para leer PDFs

# Logger específico de este módulo
logger = logging.getLogger(__name__)


def read_faq_csv(path: Path) -> List[Dict[str, str]]:
    """
    Lee un CSV de FAQs y devuelve una lista de diccionarios.

    Formato esperado del CSV:
        pregunta,respuesta,categoria
        ¿Cómo me inscribo?,Entra a Moodle...,Inscripción

    Si el archivo no existe o está vacío, devuelve lista vacía
    (no lanza excepción para no romper el arranque).
    """
    # Validamos existencia antes de intentar leer
    if not path.exists():
        logger.warning("Archivo FAQ no encontrado en %s", path)
        return []

    try:
        # Leemos el CSV. encoding='utf-8' soporta tildes y eñes
        df = pd.read_csv(path, encoding="utf-8")

        # Verificamos que tenga las columnas mínimas requeridas
        required = {"pregunta", "respuesta"}
        if not required.issubset(df.columns):
            logger.error(
                "El CSV debe tener las columnas %s. Encontradas: %s",
                required, list(df.columns),
            )
            return []

        # Si no hay columna 'categoria', añadimos una vacía
        if "categoria" not in df.columns:
            df["categoria"] = ""

        # Eliminamos filas donde la pregunta o respuesta estén vacías
        df = df.dropna(subset=["pregunta", "respuesta"])

        # Convertimos el DataFrame a lista de dicts (más fácil de manejar)
        return df[["pregunta", "respuesta", "categoria"]].to_dict(orient="records")

    except Exception as exc:
        # Capturamos cualquier error de parseo para no tumbar el server
        logger.exception("Error leyendo FAQ CSV: %s", exc)
        return []


def read_calendar_xlsx(path: Path) -> List[Dict[str, str]]:
    """
    Lee un Excel de calendario académico.

    Formato esperado:
        actividad | fecha | asignatura | enlace

    Devuelve lista de dicts con todas las columnas como string.
    """
    if not path.exists():
        logger.warning("Calendario no encontrado en %s", path)
        return []

    try:
        # Leemos solo la primera hoja del XLSX
        df = pd.read_excel(path, sheet_name=0, engine="openpyxl")

        # Convertimos todo a string para evitar problemas con fechas/NaN
        df = df.astype(str).fillna("")

        return df.to_dict(orient="records")

    except Exception as exc:
        logger.exception("Error leyendo calendario XLSX: %s", exc)
        return []


def read_pdf_text(path: Path, max_pages: int = 50) -> str:
    """
    Extrae texto plano de un PDF (típicamente el reglamento).

    max_pages: límite de páginas para evitar leer PDFs gigantes
               que saturarían el contexto del modelo de IA.

    Devuelve un único string con todo el texto concatenado.
    """
    if not path.exists():
        logger.warning("PDF no encontrado en %s", path)
        return ""

    try:
        reader = PdfReader(str(path))
        # Iteramos las páginas hasta el límite
        chunks = []
        for i, page in enumerate(reader.pages[:max_pages]):
            text = page.extract_text() or ""    # extract_text puede devolver None
            if text.strip():
                chunks.append(text)

        full_text = "\n\n".join(chunks)
        logger.info("PDF leído: %d páginas, %d caracteres", len(chunks), len(full_text))
        return full_text

    except Exception as exc:
        logger.exception("Error leyendo PDF: %s", exc)
        return ""
