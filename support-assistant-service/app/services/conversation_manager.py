from app.models.conversation import Conversation
from app.repositories.conversation_repository import ConversationRepository


class ConversationManager:
    def __init__(self, repository: ConversationRepository, recent_messages: int) -> None:
        self.repository = repository
        self.recent_messages = recent_messages

    def load_or_create(self, conversation_id: str, user_id: str) -> Conversation:
        return self.repository.get(conversation_id) or self.repository.create(Conversation(conversation_id=conversation_id, user_id=user_id))

    def persist_user_message(self, conversation_id: str, message: str) -> None:
        self.repository.add_message(conversation_id, "user", message)

    def recent(self, conversation_id: str) -> list[dict]:
        return self.repository.messages(conversation_id, self.recent_messages)[0]
