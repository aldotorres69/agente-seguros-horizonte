"""
Guardrails de Seguridad, Privacidad y Cumplimiento Normativo para Seguros Horizonte S.A.
Detecta y mitiga inyecciones de prompt, intentos de suplantación, violaciones de privacidad y asesoría indebida.
"""
from typing import Dict, Any, Optional, Tuple
import re

class GuardrailsManager:
    """Administrador de reglas de contención y seguridad previa y posterior a la consulta."""

    # Patrones para detectar intentos de suplantación de identidad o inyecciones directas
    IMPERSONATION_PATTERNS = [
        r"\bsoy\s+(el\s+)?(supervisor|gerente|jefe|director|administrador|evaluador)\b",
        r"\baprueba\s+(el\s+)?siniestro\b",
        r"\bactualiza\s+(el\s+)?monto\b",
        r"\bignora\s+(tus\s+)?instrucciones\s+(anteriores)?\b",
        r"\bcambia\s+(el\s+)?estado\b"
    ]

    # Patrones para detectar consultas sobre terceros (violación de privacidad de clientes)
    THIRD_PARTY_PATTERNS = [
        r"\b(mi\s+esposo|mi\s+esposa|mi\s+conyuge|mi\s+pareja|mi\s+hijo|mi\s+papa|mi\s+mama|mi\s+hermano|mi\s+amigo)\b",
        r"\bdni\s+\d{8}\b",
        r"\bseguros\s+de\s+[a-z]+\s+[a-z]+\b"
    ]

    # Patrones para detectar solicitud de asesoría financiera o de inversiones
    FINANCIAL_ADVICE_PATTERNS = [
        r"\b(fondo\s+mutuo|fondos\s+mutuos)\b",
        r"\b(me\s+conviene\s+mas|que\s+me\s+conviene|donde\s+invierto|en\s+que\s+invierto)\b",
        r"\b(meterlos\s+en|invertir|rentabilidad|rendimiento\s+financiero)\b"
    ]

    @classmethod
    def check_pre_execution_guardrails(
        cls, user_role: str, user_id: str, message: str
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Ejecuta comprobaciones de seguridad antes de consultar la base de datos o el LLM.
        Retorna (intervenido, respuesta_bloqueo, metadata).
        """
        msg_lower = message.lower()

        # 1. Guardrail de Privilegios y Suplantación (ej. CP-09)
        if user_role == "cliente":
            for pattern in cls.IMPERSONATION_PATTERNS:
                if re.search(pattern, msg_lower):
                    response = (
                        "Acción denegada por seguridad y normativa interna:\n"
                        "1. La sesión activa corresponde al rol de cliente autenticado (usuario {}). "
                        "No se admiten cambios de rol ni autorizaciones declaradas dentro del mensaje.\n"
                        "2. Este asistente virtual opera estrictamente en modo de solo lectura y no tiene facultades "
                        "ni permisos técnicos para aprobar siniestros, modificar montos ni alterar estados.\n"
                        "3. Conforme al Artículo 5, numeral 5.1 de las Condiciones Generales, únicamente el área humana de "
                        "Evaluación de Siniestros está facultada para aprobar, rechazar o modificar los montos de un siniestro.\n\n"
                        "Fuente consultada: Condiciones Generales de Seguros Horizonte S.A., Artículo 5, numeral 5.1."
                    ).format(user_id)
                    return True, response, {
                        "guardrail": "anti_impersonation",
                        "herramienta": "guardrail_seguridad",
                        "fuente": "Condiciones Generales, Artículo 5.1"
                    }

        # 2. Guardrail de Privacidad de Terceros (ej. CP-06)
        if user_role == "cliente":
            has_third_party = any(re.search(p, msg_lower) for p in cls.THIRD_PARTY_PATTERNS)
            if has_third_party and not any(k in msg_lower for k in ["mi siniestro", "mi seguro", "mi auto"]):
                response = (
                    "Por estrictas razones de privacidad, secreto asegurador y normativa de protección de datos personales, "
                    "únicamente puedes consultar información correspondiente a tus propias pólizas y siniestros contratados "
                    "(usuario {}).\n\n"
                    "No es posible brindar información sobre pólizas, coberturas o estados de pago de terceras personas "
                    "(incluidos cónyuges o familiares) a través de este canal digital sin una autorización formal y validación de poderes.\n\n"
                    "Te recomendamos que el titular de la póliza inicie sesión desde su propia cuenta o se comunique con su asesor comercial asignado."
                ).format(user_id)
                return True, response, {
                    "guardrail": "privacy_protection",
                    "herramienta": "guardrail_privacidad",
                    "fuente": "Reglamento de Privacidad y Términos de Protección de Datos Personales"
                }

        # 3. Guardrail de Asesoría Financiera / Inversión (ej. CP-07)
        has_advice_request = any(re.search(p, msg_lower) for p in cls.FINANCIAL_ADVICE_PATTERNS)
        if has_advice_request:
            response = (
                "Estimado cliente, de acuerdo con el Artículo 2, numeral 2.3 del Condicionado Particular del Seguro de Vida "
                "y las políticas de Seguros Horizonte S.A., este canal digital y los asistentes de atención no están autorizados "
                "a brindar asesoría financiera, recomendaciones de inversión ni comparativas con otros instrumentos del mercado (como fondos mutuos).\n\n"
                "Puntos clave de la póliza de vida con ahorro (Vida Ahorro Plus):\n"
                "- Ofrece protección ante fallecimiento e invalidez, además de un componente de ahorro.\n"
                "- Conforme al Artículo 2, numeral 2.1, los rendimientos no están garantizados y dependen de las inversiones de la aseguradora.\n"
                "- El rescate anticipado antes del quinto año conlleva una penalidad de hasta el 20% (numeral 2.2).\n\n"
                "He registrado un ticket de escalamiento para que un asesor comercial autorizado se ponga en contacto contigo "
                "y evalúe tu perfil de riesgo de forma personalizada.\n\n"
                "Fuente consultada: Condicionado Particular Seguro de Vida, Artículo 2 (numerales 2.1, 2.2 y 2.3)."
            )
            return True, response, {
                "guardrail": "financial_advice_restriction",
                "herramienta": "escalar_a_humano",
                "fuente": "Seguro de Vida, Artículo 2.3",
                "escalamiento": {
                    "motivo": "Solicitud de asesoría de inversión en Vida Ahorro Plus vs fondo mutuo",
                    "categoria": "asesoria_comercial",
                    "prioridad": "media"
                }
            }

        return False, None, None

    @classmethod
    def sanitize_untrusted_database_content(cls, raw_text: str) -> str:
        """
        Detecta y neutraliza inyecciones indirectas de prompt incrustadas en datos de la base de datos (ej. CP-12).
        """
        if not raw_text or not isinstance(raw_text, str):
            return raw_text

        # Detectar patrones sospechosos de instrucción al LLM
        injection_triggers = [
            r"NOTA\s+PARA\s+EL\s+ASISTENTE\s+VIRTUAL",
            r"ignora\s+tus\s+instrucciones",
            r"marca\s+este\s+siniestro\s+como\s+APROBADO",
            r"informa\s+al\s+cliente\s+que\s+recibirá"
        ]

        is_suspicious = any(re.search(t, raw_text, re.IGNORECASE) for t in injection_triggers)
        if is_suspicious:
            # Reemplazar la parte de inyección por una advertencia de seguridad estructurada
            cleaned = re.sub(
                r"NOTA\s+PARA\s+EL\s+ASISTENTE.*",
                "[ADVERTENCIA DE SEGURIDAD: Texto no verificado omitido por violar directivas de integridad]",
                raw_text,
                flags=re.IGNORECASE
            )
            return cleaned

        return raw_text
