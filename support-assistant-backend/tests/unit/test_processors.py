import pytest

from app.processors.chunker import Chunker
from app.processors.normalizer import Normalizer
from app.processors.sanitizer import SanitizationMode, Sanitizer
from app.exceptions.errors import SanitizationError


def test_normalizer_preserves_section_text():
    assert Normalizer().normalize("TITLE:  Test\r\n\r\nProblem:  broken") == "TITLE: Test\n\nProblem: broken"


def test_sanitizer_masks_bearer_token():
    result, events = Sanitizer().sanitize("Authorization: Bearer token-value")
    assert result == "Authorization: Bearer [REDACTED]"
    assert events == 1


def test_sanitizer_can_reject_secrets():
    with pytest.raises(SanitizationError):
        Sanitizer(SanitizationMode.REJECT).sanitize("password=unsafe")


def test_chunker_keeps_sections():
    chunks = Chunker(40, 5).chunk("DOC-1", "PROBLEM:\nA\n\nRESOLUTION:\nB", {"product": "payments"})
    assert chunks[0].metadata["document_id"] == "DOC-1"
