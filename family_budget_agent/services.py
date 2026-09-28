"""Persistencia, sesiones y Memory Bank según el perfil activo.

Las sesiones siempre usan `DatabaseSessionService` (SQLite en local; apuntar
`SESSION_DB_URL` a PostgreSQL/Cloud SQL en producción). La memoria a largo
plazo se resuelve en `config.build_memory_service()`: `InMemoryMemoryService`
en local y `VertexAiMemoryBankService` en producción.
"""

from google.adk.sessions import DatabaseSessionService

from . import config

APP_NAME = "family_budget_agent"
USER_ID = "family_admin_1"


def initialize_persistence_and_memory():
    """Configura los servicios de sesión SQL persistente y memoria a largo plazo."""
    session_service = DatabaseSessionService(db_url=config.SESSION_DB_URL)
    memory_bank_service = config.build_memory_service()
    return session_service, memory_bank_service


async def create_user_session(session_service):
    """Crea la sesión con el estado `user:` que espera el orquestador."""
    return await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        state={
            "user:id": USER_ID,
            "user:role": "parent_admin",
            "user:monthly_budget_limit": 2500.0,
            "user:savings_target_monthly": 500.0,
        },
    )
