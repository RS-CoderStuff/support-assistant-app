import json

import boto3


class SQSService:
    def __init__(self, queue_url: str, region: str) -> None:
        self.queue_url = queue_url
        self.client = boto3.client("sqs", region_name=region)

    def enqueue(self, job_id: str) -> None:
        self.enqueue_payload({"job_id": job_id})

    def enqueue_payload(self, payload: dict) -> None:
        self.client.send_message(QueueUrl=self.queue_url, MessageBody=json.dumps(payload))

    def receive(self) -> list[dict]:
        return self.client.receive_message(QueueUrl=self.queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=10).get("Messages", [])

    def delete(self, receipt_handle: str) -> None:
        self.client.delete_message(QueueUrl=self.queue_url, ReceiptHandle=receipt_handle)
