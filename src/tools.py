"""
Definición e implementación de las herramientas (Tools) del Agente de Seguros Horizonte S.A.
Compatible con OpenAI Function Calling / LangChain / frameworks agénticos.
"""
from typing import Dict, Any, List, Optional
import json
import uuid
from src.database import DuckDBProvider
from src.search import PolicySearchEngine
from src.guardrails import GuardrailsManager

class ToolManager:
    """Administrador centralizado de herramientas con inyección de contexto de sesión."""

    def __init__(self, db: DuckDBProvider, search_engine: PolicySearchEngine):
        self.db = db
        self.search_engine = search_engine
        self.escalated_tickets: List[Dict[str, Any]] = []

    def execute_sql(self, sql: str, user_role: str, user_id: str) -> str:
        """
        Ejecuta una consulta SQL de solo lectura sobre las tablas de clientes, pólizas, siniestros y asesores.
        Aplica automáticamente restricciones de seguridad y privacidad según el rol.
        """
        try:
            results = self.db.execute_query(sql, user_role, user_id)
            # Sanitizar posibles inyecciones indirectas en descripciones de siniestros
            for row in results:
                if isinstance(row, dict) and "descripcion" in row and isinstance(row["descripcion"], str):
                    row["descripcion"] = GuardrailsManager.sanitize_untrusted_database_content(row["descripcion"])
            return json.dumps(results, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def search_conditions(self, query: str, ramo: Optional[str] = None) -> str:
        """
        Busca en los condicionados (Condiciones Generales, Vehicular, Salud, Vida) los artículos relevantes.
        """
        try:
            results = self.search_engine.search(query, ramo=ramo, top_k=3)
            if not results:
                return json.dumps({"mensaje": "No se encontraron cláusulas relevantes para la consulta."}, ensure_ascii=False)
            return json.dumps(results, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def escalate_ticket(self, user_role: str, user_id: str, motivo: str, categoria: str, prioridad: str = "media") -> str:
        """
        Registra un ticket de escalamiento hacia un asesor comercial o evaluador de siniestros humano.
        """
        ticket_id = f"TK-{uuid.uuid4().hex[:6].upper()}"
        ticket = {
            "ticket_id": ticket_id,
            "usuario_id": user_id,
            "rol": user_role,
            "motivo": motivo,
            "categoria": categoria,
            "prioridad": prioridad,
            "estado": "pendiente_atencion",
            "fecha_registro": "2026-10-15"
        }
        self.escalated_tickets.append(ticket)
        return json.dumps({
            "mensaje": f"Ticket {ticket_id} registrado exitosamente para atención por un especialista humano.",
            "ticket": ticket
        }, ensure_ascii=False)

    @classmethod
    def get_openai_tools_schema(cls) -> List[Dict[str, Any]]:
        """Retorna el esquema JSON de herramientas para OpenAI / LLMs compatibles."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "consulta_datos_sql",
                    "description": "Ejecuta consultas SQL de solo lectura sobre clientes, polizas, siniestros y asesores. Obligatorio para consultar estado de pólizas, reclamos o métricas.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Consulta SQL SELECT válida. Ej: SELECT * FROM polizas WHERE cliente_id = 'C001'"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "busqueda_condicionados",
                    "description": "Busca fragmentos y artículos relevantes en las Condiciones Generales y condicionados particulares de Vehicular, Salud y Vida.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Términos o conceptos a buscar (ej: choque contra poste, cirugía de vesícula, periodos de carencia, robo total, exclusiones)"
                            },
                            "ramo": {
                                "type": "string",
                                "enum": ["vehicular", "salud", "vida", "general"],
                                "description": "Opcional: filtrar por ramo específico"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "escalar_a_humano",
                    "description": "Registra un ticket para derivar la atención a un asesor comercial, evaluador médico o analista de siniestros humano cuando la consulta lo requiera.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "motivo": {
                                "type": "string",
                                "description": "Motivo detallado del escalamiento"
                            },
                            "categoria": {
                                "type": "string",
                                "enum": ["asesoria_comercial", "evaluacion_siniestro", "soporte_legal", "atencion_personalizada"],
                                "description": "Área a la cual dirigir el ticket"
                            },
                            "prioridad": {
                                "type": "string",
                                "enum": ["baja", "media", "alta", "urgente"],
                                "description": "Nivel de prioridad del ticket"
                            }
                        },
                        "required": ["motivo", "categoria"]
                    }
                }
            }
        ]
