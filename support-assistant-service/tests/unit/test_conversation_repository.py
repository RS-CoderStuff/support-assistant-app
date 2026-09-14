from decimal import Decimal
from unittest.mock import Mock

from app.models.conversation import Conversation
from app.repositories.conversation_repository import DynamoDBConversationRepository


def test_dynamodb_save_converts_nested_floats_to_decimals() -> None:
    table = Mock()
    repository = DynamoDBConversationRepository(table)
    conversation = Conversation(
        conversation_id="CONV-1",
        user_id="USER-1",
        active_evidence=[{"source_id": "DOC-1", "relevance_score": 0.92}],
    )

    repository.save(conversation)

    item = table.put_item.call_args.kwargs["Item"]
    assert item["active_evidence"][0]["relevance_score"] == Decimal("0.92")