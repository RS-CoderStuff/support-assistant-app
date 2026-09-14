import boto3

from app.config.settings import Settings


class DynamoDBClient:
    def __init__(self, settings: Settings) -> None:
        if not settings.conversation_table_name:
            raise ValueError("SUPPORT_ASSISTANT_CONVERSATION_TABLE_NAME is required outside development mode")
        self.table = boto3.resource("dynamodb", region_name=settings.aws_region).Table(settings.conversation_table_name)
