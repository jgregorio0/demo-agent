"""Persistencia, sesiones y Memory Bank."""

from google.adk.sessions import DatabaseSessionService
from google.adk.memory import VertexAiMemoryBankService


def initialize_persistence_and_memory():
    """Configura los servicios de sesión SQL persistente y Memory Bank para retención a largo plazo."""
    session_service = DatabaseSessionService(
        db_url="sqlite+aiosqlite:///./family_budget_sessions.db"
    )

    memory_bank_service = VertexAiMemoryBankService(
        project_id="demo-family-finance-gcp",
        location="us-central1"
    )

    return session_service, memory_bank_service
