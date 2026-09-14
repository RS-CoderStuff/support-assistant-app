from app.models.conversation import Conversation
from app.repositories.conversation_repository import ConversationRepository


class ConversationUpdater:
    def __init__(self, repository: ConversationRepository) -> None:
        self.repository = repository

    def update(self, conversation: Conversation, answer: str, current_issue: dict, citations: list[dict]) -> None:
        conversation.current_issue = current_issue
        conversation.active_evidence = citations
        conversation.summary = f"Latest issue: {current_issue}."
        self.repository.add_message(conversation.conversation_id, "assistant", answer)
        self.repository.save(conversation)
