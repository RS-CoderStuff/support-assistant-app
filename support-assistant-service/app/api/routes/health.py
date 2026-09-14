from fastapi import APIRouter

from app.config.settings import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def ready() -> dict[str, str]:
    settings = get_settings()
    status = "ready" if settings.environment == "dev" or (settings.knowledge_base_id and settings.conversation_table_name) else "not_ready"
    return {"status": status}
