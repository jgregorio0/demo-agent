"""Perfiles de ejecución del agente.

`AGENT_PROFILE=local` (por defecto): todo en local y gratuito — LLM vía
Ollama/LiteLLM, RAG con ChromaDB + embeddings ONNX locales (u Ollama),
executor de código local (o Docker), memoria en proceso y sesiones en SQLite.

`AGENT_PROFILE=production`: infraestructura gestionada de GCP — Gemini en
Vertex AI, Vertex AI Search, Agent Engine Sandbox y Vertex AI Memory Bank.
Requiere proyecto GCP con billing y credenciales (Application Default
Credentials o GOOGLE_API_KEY).

Orden de carga de variables: `.env` (defaults, incluido AGENT_PROFILE) y
después `.env.<perfil>` (`.env.local` / `.env.production`) con override.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

_BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(_BASE_DIR / ".env")
PROFILE = os.getenv("AGENT_PROFILE", "local").strip().lower()
load_dotenv(_BASE_DIR / f".env.{PROFILE}", override=True)

_VALID_PROFILES = ("local", "production")
if PROFILE not in _VALID_PROFILES:
    raise ValueError(f"AGENT_PROFILE inválido: '{PROFILE}'. Usa 'local' o 'production'.")

IS_PRODUCTION = PROFILE == "production"

# ---------------------------------------------------------------------------
# Identificadores GCP (solo relevantes en perfil production)
# ---------------------------------------------------------------------------
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "demo-family-finance-gcp")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
VERTEX_SEARCH_DATA_STORE = os.getenv("VERTEX_SEARCH_DATA_STORE", "family-finance-guides-ds")

# ---------------------------------------------------------------------------
# Modelos
# ---------------------------------------------------------------------------
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "ollama_chat/llama3.1:8b")
OLLAMA_API_BASE = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
# Si se define, los embeddings del RAG local se generan con Ollama;
# en caso contrario se usa el embedding ONNX por defecto de ChromaDB.
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "")

PROD_MODELS = {
    "orchestrator": os.getenv("GEMINI_ORCHESTRATOR_MODEL", "gemini-2.5-flash"),
    "advisor": os.getenv("GEMINI_ADVISOR_MODEL", "gemini-2.5-flash"),
    "analyst": os.getenv("GEMINI_ANALYST_MODEL", "gemini-2.5-pro"),
}
LOCAL_MODELS = {
    "orchestrator": os.getenv("LOCAL_ORCHESTRATOR_MODEL", LOCAL_LLM_MODEL),
    "advisor": os.getenv("LOCAL_ADVISOR_MODEL", LOCAL_LLM_MODEL),
    "analyst": os.getenv("LOCAL_ANALYST_MODEL", LOCAL_LLM_MODEL),
}

# ---------------------------------------------------------------------------
# Resto de infraestructura
# ---------------------------------------------------------------------------
SESSION_DB_URL = os.getenv("SESSION_DB_URL", "sqlite+aiosqlite:///./family_budget_sessions.db")
# "local" → UnsafeLocalCodeExecutor (sin aislamiento) | "docker" → ContainerCodeExecutor
CODE_EXECUTOR_MODE = os.getenv("CODE_EXECUTOR_MODE", "local").strip().lower()

logger.info("[CONFIG] Perfil activo: %s", PROFILE)


def get_model(role: str):
    """Devuelve el modelo para el rol ('orchestrator' | 'advisor' | 'analyst').

    En local se envuelve en LiteLlm apuntando a Ollama; en producción se
    devuelve el nombre del modelo Gemini (resuelto por ADK vía Vertex AI).
    """
    if IS_PRODUCTION:
        return PROD_MODELS[role]
    os.environ.setdefault("OLLAMA_API_BASE", OLLAMA_API_BASE)
    from google.adk.models.lite_llm import LiteLlm

    return LiteLlm(model=LOCAL_MODELS[role], api_base=OLLAMA_API_BASE)


def get_model_label(role: str = "orchestrator") -> str:
    """Etiqueta legible del modelo activo (para logging/summary)."""
    model = (PROD_MODELS if IS_PRODUCTION else LOCAL_MODELS)[role]
    return f"{model} ({'Vertex AI' if IS_PRODUCTION else 'Ollama'})"


def build_search_tool():
    """RAG: VertexAiSearchTool en producción; ChromaDB+embeddings locales en local."""
    if IS_PRODUCTION:
        from google.adk.tools import VertexAiSearchTool

        # bypass_multi_tools_limit: se combina con FunctionTools en el advisor.
        return VertexAiSearchTool(
            data_store_id=VERTEX_SEARCH_DATA_STORE,
            bypass_multi_tools_limit=True,
        )
    from google.adk.tools import FunctionTool

    from .knowledge_base import search_family_finance_guides

    return FunctionTool(func=search_family_finance_guides)


def build_code_executor():
    """Executor de código: Agent Engine Sandbox en producción; local/Docker en local."""
    if IS_PRODUCTION:
        from google.adk.code_executors import AgentEngineSandboxCodeExecutor

        # Sin sandbox_resource_name, el executor auto-crea un sandbox por
        # sesión (evita fugas de estado entre usuarios). Para reutilizar uno
        # fijo, definir AGENT_ENGINE_SANDBOX con el resource name completo.
        sandbox = os.getenv("AGENT_ENGINE_SANDBOX", "")
        if sandbox:
            return AgentEngineSandboxCodeExecutor(sandbox_resource_name=sandbox)
        return AgentEngineSandboxCodeExecutor()

    if CODE_EXECUTOR_MODE == "docker":
        try:
            from google.adk.code_executors import ContainerCodeExecutor

            return ContainerCodeExecutor()
        except Exception as exc:
            logger.warning(
                "[CONFIG] ContainerCodeExecutor no disponible (%s); "
                "se usa UnsafeLocalCodeExecutor.",
                exc,
            )
    elif CODE_EXECUTOR_MODE != "local":
        logger.warning(
            "[CONFIG] CODE_EXECUTOR_MODE='%s' desconocido; se usa 'local'.",
            CODE_EXECUTOR_MODE,
        )
    from google.adk.code_executors import UnsafeLocalCodeExecutor

    return UnsafeLocalCodeExecutor()


def build_memory_service():
    """Memoria a largo plazo: VertexAiMemoryBankService en producción; en proceso en local.

    Memory Bank va ligado a un Agent Engine desplegado: en producción exige
    `AGENT_ENGINE_ID` (o GOOGLE_CLOUD_AGENT_ENGINE_ID) en el entorno.
    """
    if IS_PRODUCTION:
        from google.adk.memory import VertexAiMemoryBankService

        agent_engine_id = os.getenv("AGENT_ENGINE_ID")
        if not agent_engine_id:
            raise ValueError(
                "AGENT_PROFILE=production requiere AGENT_ENGINE_ID para "
                "VertexAiMemoryBankService (ID del Agent Engine desplegado)."
            )
        return VertexAiMemoryBankService(
            project=GCP_PROJECT_ID,
            location=GCP_LOCATION,
            agent_engine_id=agent_engine_id,
        )
    from google.adk.memory import InMemoryMemoryService

    return InMemoryMemoryService()
