from types import SimpleNamespace
from unittest.mock import patch

from app.aws.bedrock_kb_client import BedrockKnowledgeBaseClient


class TestBedrockKnowledgeBaseClient:
    """Tests for BedrockKnowledgeBaseClient configuration building."""

    @staticmethod
    def _create_client(retrieval_mode: str) -> BedrockKnowledgeBaseClient:
        settings = SimpleNamespace(aws_region="us-east-1", knowledge_base_retrieval_mode=retrieval_mode)
        with patch("app.aws.bedrock_kb_client.boto3.client"):
            return BedrockKnowledgeBaseClient(settings)

    def test_build_retrieval_configuration_managed_mode(self):
        """Should use managedSearchConfiguration for managed knowledge bases."""
        client = self._create_client("managed")
        config = client._build_retrieval_configuration(metadata_filter=None, top_k=5)

        assert "managedSearchConfiguration" in config
        assert "vectorSearchConfiguration" not in config
        assert config["managedSearchConfiguration"]["numberOfResults"] == 5

    def test_build_retrieval_configuration_vector_mode(self):
        """Should use vectorSearchConfiguration for vector knowledge bases."""
        client = self._create_client("vector")
        config = client._build_retrieval_configuration(metadata_filter=None, top_k=10)

        assert "vectorSearchConfiguration" in config
        assert "managedSearchConfiguration" not in config
        assert config["vectorSearchConfiguration"]["numberOfResults"] == 10

    def test_build_retrieval_configuration_with_filter(self):
        """Should include filter in search configuration."""
        client = self._create_client("managed")
        test_filter = {"equals": {"key": "source_type", "value": "faq"}}
        config = client._build_retrieval_configuration(metadata_filter=test_filter, top_k=5)

        assert config["managedSearchConfiguration"]["filter"] == test_filter

    def test_build_retrieval_configuration_no_filter_when_none(self):
        """Should not include filter key when metadata_filter is None."""
        client = self._create_client("managed")
        config = client._build_retrieval_configuration(metadata_filter=None, top_k=5)

        assert "filter" not in config["managedSearchConfiguration"]
