"""
Sistema de Logging y Auditoría de Interacciones para Seguros Horizonte S.A.
Registra cada consulta, rol, herramientas invocadas, fuentes y métricas de consumo.
"""
from typing import Dict, Any, List, Optional
import json
import time
from datetime import datetime
from pathlib import Path
from src.config import LOGS_DIR

class AuditLogger:
    """Registrador de auditoría en formato JSONL para trazabilidad y cumplimiento regulatorio."""

    def __init__(self, log_path: Path = LOGS_DIR / "interacciones.jsonl"):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_interaction(
        self,
        caso_id: Optional[str],
        rol: str,
        usuario_id: str,
        mensaje: str,
        herramientas_usadas: List[Dict[str, Any]],
        fuentes_citadas: List[str],
        respuesta: str,
        duracion_ms: float,
        tokens_in: int = 0,
        tokens_out: int = 0,
        modelo: str = "gpt-4o-mini"
    ) -> Dict[str, Any]:
        """Escribe un registro de interacción en formato JSONL."""
        # Estimar costo en base a tarifas estándar de gpt-4o-mini ($0.15/1M in, $0.60/1M out)
        costo_usd = (tokens_in * 0.00000015) + (tokens_out * 0.00000060)

        entry = {
            "timestamp": datetime.now().isoformat(),
            "caso_id": caso_id,
            "rol": rol,
            "usuario_id": usuario_id,
            "mensaje": mensaje,
            "herramientas_usadas": [h.get("nombre", h.get("tool", "desconocida")) for h in herramientas_usadas],
            "detalle_herramientas": herramientas_usadas,
            "fuentes_citadas": fuentes_citadas,
            "respuesta": respuesta,
            "metricas": {
                "duracion_ms": round(duracion_ms, 2),
                "tokens_entrada": tokens_in,
                "tokens_salida": tokens_out,
                "tokens_totales": tokens_in + tokens_out,
                "costo_estimado_usd": round(costo_usd, 6),
                "modelo": modelo
            }
        }

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        return entry

    def get_recent_logs(self, limit: int = 12) -> List[Dict[str, Any]]:
        """Lee los últimos registros de interacción."""
        if not self.log_path.exists():
            return []
        entries = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entries.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
        return entries[-limit:]
