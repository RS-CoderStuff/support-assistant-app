class KnowledgeProcessingError(Exception):
    code = "KNOWLEDGE_PROCESSING_ERROR"


class UnsupportedFileTypeError(KnowledgeProcessingError):
    code = "UNSUPPORTED_FILE_TYPE"


class ParserError(KnowledgeProcessingError):
    code = "PARSER_ERROR"


class InvalidDocumentError(KnowledgeProcessingError):
    code = "INVALID_DOCUMENT"


class S3StorageError(KnowledgeProcessingError):
    code = "S3_STORAGE_ERROR"


class MetadataValidationError(KnowledgeProcessingError):
    code = "METADATA_VALIDATION_ERROR"


class SanitizationError(KnowledgeProcessingError):
    code = "SANITIZATION_ERROR"


class KnowledgeBaseSyncError(KnowledgeProcessingError):
    code = "KNOWLEDGE_BASE_SYNC_ERROR"
