from functools import lru_cache

from app.config.settings import get_settings
from app.parsers.csv_parser import CSVParser
from app.parsers.json_parser import JSONParser
from app.parsers.log_parser import LogParser
from app.parsers.markdown_parser import MarkdownParser
from app.parsers.pdf_parser import PDFParser
from app.parsers.registry import ParserRegistry
from app.parsers.text_parser import TextParser
from app.processors.chunker import Chunker
from app.processors.metadata import MetadataEnricher
from app.processors.normalizer import Normalizer
from app.processors.sanitizer import SanitizationMode, Sanitizer
from app.queue.sqs_service import SQSService
from app.services.knowledge_ingestion_service import KnowledgeIngestionService
from app.storage.dynamodb_repository import DynamoDBJobRepository
from app.storage.s3_service import S3Service


@lru_cache
def get_s3() -> S3Service:
    config = get_settings()
    return S3Service(config.raw_bucket, config.enriched_bucket, config.aws_region)


@lru_cache
def get_jobs() -> DynamoDBJobRepository:
    config = get_settings()
    return DynamoDBJobRepository(config.dynamodb_table, config.aws_region)


@lru_cache
def get_queue() -> SQSService:
    config = get_settings()
    return SQSService(config.ingestion_queue_url, config.aws_region)


@lru_cache
def get_ingestion_service() -> KnowledgeIngestionService:
    mode = SanitizationMode(get_settings().sanitizer_mode)
    return KnowledgeIngestionService(ParserRegistry(  [JSONParser(), PDFParser(), LogParser(), CSVParser(), MarkdownParser(), TextParser()]), Normalizer(), Sanitizer(mode), MetadataEnricher(), Chunker(), get_s3(), get_jobs())
