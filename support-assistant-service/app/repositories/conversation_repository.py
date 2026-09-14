from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Protocol

from app.exceptions.exceptions import ConversationNotFoundException
from app.models.conversation import Conversation


def _to_dynamodb_value(value: Any) -> Any:
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {key: _to_dynamodb_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_dynamodb_value(item) for item in value]
    return value


class ConversationRepository(Protocol):
    def get(self, conversation_id: str) -> Conversation | None: ...
    def create(self, conversation: Conversation) -> Conversation: ...
    def save(self, conversation: Conversation) -> None: ...
    def add_message(self, conversation_id: str, role: str, content: str) -> None: ...
    def messages(self, conversation_id: str, limit: int, cursor: str | None = None) -> tuple[list[dict], str | None]: ...
    def close(self, conversation_id: str) -> None: ...


class InMemoryConversationRepository:
    def __init__(self) -> None:
        self.conversations: dict[str, Conversation] = {}
        self.message_store: dict[str, list[dict]] = {}

    def get(self, conversation_id: str) -> Conversation | None:
        return self.conversations.get(conversation_id)

    def create(self, conversation: Conversation) -> Conversation:
        now = datetime.now(UTC).isoformat()
        conversation.created_at = now
        conversation.updated_at = now
        self.conversations[conversation.conversation_id] = conversation
        return conversation

    def save(self, conversation: Conversation) -> None:
        conversation.updated_at = datetime.now(UTC).isoformat()
        self.conversations[conversation.conversation_id] = conversation

    def add_message(self, conversation_id: str, role: str, content: str) -> None:
        messages = self.message_store.setdefault(conversation_id, [])
        messages.append({"sequence": len(messages) + 1, "role": role, "content": content, "created_at": datetime.now(UTC).isoformat()})

    def messages(self, conversation_id: str, limit: int, cursor: str | None = None) -> tuple[list[dict], str | None]:
        items = self.message_store.get(conversation_id, [])
        start = int(cursor or 0)
        page = items[start:start + limit]
        next_cursor = str(start + limit) if start + limit < len(items) else None
        return page, next_cursor

    def close(self, conversation_id: str) -> None:
        conversation = self.get(conversation_id)
        if not conversation:
            raise ConversationNotFoundException()
        conversation.status = "CLOSED"
        self.save(conversation)


class DynamoDBConversationRepository:
    def __init__(self, table) -> None:
        self.table = table

    def get(self, conversation_id: str) -> Conversation | None:
        item = self.table.get_item(Key={"PK": f"CONVERSATION#{conversation_id}", "SK": "METADATA"}).get("Item")
        if not item:
            return None
        return Conversation(conversation_id=item["conversation_id"], user_id=item["user_id"], status=item["status"], summary=item.get("summary", ""), current_issue=item.get("current_issue", {}), active_evidence=item.get("active_evidence", []), created_at=item.get("created_at"), updated_at=item.get("updated_at"))

    def create(self, conversation: Conversation) -> Conversation:
        now = datetime.now(UTC).isoformat()
        conversation.created_at = now
        conversation.updated_at = now
        self.save(conversation)
        return conversation

    def save(self, conversation: Conversation) -> None:
        conversation.updated_at = datetime.now(UTC).isoformat()
        item = {"PK": f"CONVERSATION#{conversation.conversation_id}", "SK": "METADATA", "conversation_id": conversation.conversation_id, "user_id": conversation.user_id, "status": conversation.status, "summary": conversation.summary, "current_issue": conversation.current_issue, "active_evidence": conversation.active_evidence, "created_at": conversation.created_at, "updated_at": conversation.updated_at}
        self.table.put_item(Item=_to_dynamodb_value(item))

    def add_message(self, conversation_id: str, role: str, content: str) -> None:
        timestamp = datetime.now(UTC).isoformat()
        self.table.put_item(Item={"PK": f"CONVERSATION#{conversation_id}", "SK": f"MESSAGE#{timestamp}", "sequence": timestamp, "role": role, "content": content, "created_at": timestamp})

    def messages(self, conversation_id: str, limit: int, cursor: str | None = None) -> tuple[list[dict], str | None]:
        parameters = {"KeyConditionExpression": "PK = :pk AND begins_with(SK, :prefix)", "ExpressionAttributeValues": {":pk": f"CONVERSATION#{conversation_id}", ":prefix": "MESSAGE#"}, "Limit": limit, "ScanIndexForward": False}
        if cursor:
            parameters["ExclusiveStartKey"] = {"PK": f"CONVERSATION#{conversation_id}", "SK": cursor}
        response = self.table.query(**parameters)
        next_cursor = response.get("LastEvaluatedKey", {}).get("SK")
        return list(reversed(response.get("Items", []))), next_cursor

    def close(self, conversation_id: str) -> None:
        conversation = self.get(conversation_id)
        if not conversation:
            raise ConversationNotFoundException()
        conversation.status = "CLOSED"
        self.save(conversation)
