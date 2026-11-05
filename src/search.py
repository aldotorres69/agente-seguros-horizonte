"""
Motor de búsqueda y recuperación sobre los documentos condicionados (RAG ligero / BM25).
Permite buscar por palabras clave, conceptos de seguros y filtrar por ramo.
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import re
import math
from src.config import CONDICIONADOS_DIR

class PolicySearchEngine:
    """Indexador y buscador de cláusulas en condicionados de seguros."""

    SYNONYMS = {
        "vesicula": ["colecistectomia", "vesicula", "cirugias programadas", "carencia", "6 meses"],
        "colecistectomia": ["vesicula", "cirugia programada", "carencia"],
        "choque": ["colision", "daño propio", "choque", "despiste", "deducible", "taller"],
        "poste": ["choque", "colision", "daños a la propiedad publica", "dosaje etilico"],
        "ebriedad": ["dosaje etilico", "alcohol", "0.5 g/l", "estado de ebriedad", "exclusion"],
        "alcohol": ["dosaje etilico", "ebriedad", "0.5 g/l"],
        "robo": ["robo total", "denuncia policial", "24 horas", "30 dias", "recuperado"],
        "ahorro": ["vida ahorro plus", "fondo mutuo", "rendimiento", "asesor comercial", "inversion"],
        "inversion": ["ahorro", "rendimiento no garantizado", "asesor comercial autorizado"],
        "vencida": ["vigencia", "fecha de fin", "no otorga cobertura", "renovacion"],
        "aprobar": ["evaluacion de siniestros", "modificar monto", "ningun canal de atencion autorizado"]
    }

    def __init__(self, condicionados_dir: Path = CONDICIONADOS_DIR):
        self.condicionados_dir = condicionados_dir
        self.documents: List[Dict[str, Any]] = []
        self._load_and_index()

    def _load_and_index(self):
        """Carga y segmenta los condicionados por artículos y secciones."""
        files = {
            "condiciones_generales.md": ("Condiciones Generales", "general"),
            "vehicular.md": ("Seguro Vehicular", "vehicular"),
            "salud.md": ("Seguro de Salud", "salud"),
            "vida.md": ("Seguro de Vida", "vida")
        }

        for filename, (doc_name, ramo) in files.items():
            path = self.condicionados_dir / filename
            if not path.exists():
                continue

            content = path.read_text(encoding="utf-8")
            # Dividir por encabezados de segundo nivel (## Artículo ...)
            sections = re.split(r"\n(?=##\s+)", content)
            for sec in sections:
                sec = sec.strip()
                if not sec:
                    continue
                match = re.match(r"##\s+(Artículo\s+\d+[^:\n]*)(?::\s*|\n)(.*)", sec, re.DOTALL)
                if match:
                    art_title = match.group(1).strip()
                    art_body = match.group(2).strip()
                else:
                    first_line = sec.split("\n")[0].replace("#", "").strip()
                    art_title = first_line
                    art_body = sec

                # Guardar fragmento indexado
                self.documents.append({
                    "documento": doc_name,
                    "archivo": filename,
                    "ramo": ramo,
                    "articulo": art_title,
                    "contenido": sec,
                    "texto_busqueda": f"{doc_name} {art_title} {art_body}".lower()
                })

    def search(self, query: str, ramo: Optional[str] = None, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Búsqueda por relevancia semántica y de palabras clave.
        Retorna los fragmentos más relevantes junto con documento y artículo exacto.
        """
        query_clean = query.lower()
        query_words = set(re.findall(r"\b\w{3,}\b", query_clean))

        # Expandir consulta con sinónimos de seguros
        expanded_words = set(query_words)
        for w in query_words:
            if w in self.SYNONYMS:
                expanded_words.update(self.SYNONYMS[w])

        scored_docs = []
        for doc in self.documents:
            # Filtrar por ramo si se especifica y no es general
            if ramo and doc["ramo"] not in [ramo.lower(), "general"]:
                continue

            score = 0.0
            doc_text = doc["texto_busqueda"]

            # Coincidencias de frases exactas
            for w in query_words:
                if w in doc_text:
                    score += 3.0

            # Coincidencias expandidas
            for ew in expanded_words:
                if ew in doc_text:
                    score += 1.5

            # Bonificación si el título del artículo coincide
            for w in query_words:
                if w in doc["articulo"].lower():
                    score += 5.0

            if score > 0:
                scored_docs.append((score, doc))

        # Ordenar por score descendente
        scored_docs.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, doc in scored_docs[:top_k]:
            results.append({
                "documento": doc["documento"],
                "archivo": doc["archivo"],
                "articulo": doc["articulo"],
                "contenido": doc["contenido"],
                "score": round(score, 2)
            })
        return results
