import boto3

from app.exceptions.errors import KnowledgeBaseSyncError


class KnowledgeBaseAdapter:
    def __init__(self, region: str) -> None:
        self.client = boto3.client("bedrock-agent", region_name=region)

    def start_ingestion(self, knowledge_base_id: str, data_source_id: str) -> dict:
        try:
            return self.client.start_ingestion_job(knowledgeBaseId=knowledge_base_id, dataSourceId=data_source_id)["ingestionJob"]
        except Exception as error:
            raise KnowledgeBaseSyncError("Unable to start knowledge base ingestion") from error

    def get_ingestion_status(self, knowledge_base_id: str, data_source_id: str, ingestion_job_id: str) -> dict:
        try:
            return self.client.get_ingestion_job(knowledgeBaseId=knowledge_base_id, dataSourceId=data_source_id, ingestionJobId=ingestion_job_id)["ingestionJob"]
        except Exception as error:
            raise KnowledgeBaseSyncError("Unable to retrieve knowledge base ingestion") from error
