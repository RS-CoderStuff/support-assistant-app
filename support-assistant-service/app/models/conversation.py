from dataclasses import dataclass, field
from typing import Any


@dataclass
class Conversation:
    conversation_id: str
    user_id: str
    status: str = "ACTIVE"
    summary: str = ""
    current_issue: dict[str, Any] = field(default_factory=dict)
    active_evidence: list[dict[str, Any]] = field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None
