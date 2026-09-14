import boto3

from app.config.settings import Settings


class BedrockRuntimeClient:
    def __init__(self, settings: Settings) -> None:
        self.client = boto3.client("bedrock-runtime", region_name=settings.aws_region)
