from datetime import datetime, timezone

import boto3

from app.models.job import IngestionJob


class DynamoDBJobRepository:
    def __init__(self, table_name: str, region: str) -> None:
        self.table = boto3.resource("dynamodb", region_name=region).Table(table_name)

    def save(self, job: IngestionJob) -> None:
        job.updated_at = datetime.now(timezone.utc)
        item = job.model_dump(mode="json")
        item.update({"PK": f"JOB#{job.job_id}", "SK": "METADATA"})
        self.table.put_item(Item=item)

    def get(self, job_id: str) -> IngestionJob | None:
        response = self.table.get_item(Key={"PK": f"JOB#{job_id}", "SK": "METADATA"})
        item = response.get("Item")
        return IngestionJob.model_validate(item) if item else None
