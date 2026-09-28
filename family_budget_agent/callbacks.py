"""Guardarraíles y callbacks de seguridad (anti-prompt injection, PII, RBAC)."""

import logging
import re
from typing import Any, Dict

from google.adk.agents.callback_context import CallbackContext

logger = logging.getLogger(__name__)


def sanitize_and_protect_input(context: CallbackContext, content: str) -> str:
    """
    Callback ejecutado ANTES de enviar la petición al LLM (before_model_callback).
    Intercepta intentos de inyección de prompts y enmascara datos sensibles (PII).
    """
    content_upper = content.upper()

    # Guardarraíl 1: Anti-Prompt Injection
    forbidden_phrases = ["IGNORA TUS INSTRUCCIONES", "SYSTEM PROMPT", "BYPASS SECURITY", "DELETE ALL TRANSACTIONS"]
    for phrase in forbidden_phrases:
        if phrase in content_upper:
            logger.warning(f"[SECURITY ALERT] Intento de inyección detectado: {phrase}")
            raise ValueError("Acción bloqueada: Se ha detectado un intento de manipulación de instrucciones o seguridad.")

    # Guardarraíl 2: Enmascaramiento de PII (Tarjetas de crédito e IBANs/Emails)
    sanitized = re.sub(r'\b(?:\d[ -]*?){13,16}\b', '[REDACTED_CREDIT_CARD]', content)
    sanitized = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[REDACTED_EMAIL]', sanitized)
    return sanitized

def enforce_tool_permissions(context: CallbackContext, tool_name: str, args: Dict[str, Any]) -> None:
    """
    Callback ejecutado ANTES de invocar una herramienta (before_tool_callback).
    Garantiza control de acceso basado en roles familiares (parent_admin vs family_member).
    """
    user_role = context.state.get("user:role", "family_member")
    if tool_name == "add_family_transaction":
        amount = args.get("amount", 0)
        # Control presupuestario: Transacciones individuales > 500 EUR requieren rol parent_admin
        if amount > 500 and user_role != "parent_admin":
            raise PermissionError(f"El usuario con rol '{user_role}' no puede registrar transacciones superiores a 500 EUR sin autorización de un administrador familiar.")
    logger.info(f"[AUDIT LOG] Herramienta '{tool_name}' autorizada para el usuario {context.state.get('user:id')}.")
