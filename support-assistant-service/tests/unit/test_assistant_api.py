from fastapi.testclient import TestClient

from app.main import app


def test_new_issue_returns_controlled_insufficient_evidence_response() -> None:
    response = TestClient(app).post("/api/v1/assistant/chat", json={
        "conversation_id": "CONV-1001",
        "user": {"user_id": "USER-123", "name": "John"},
        "message": "Why is the Payment API returning HTTP 503 after deployment?",
        "context": {"product": "payments", "component": "payment-api", "environment": "production"},
    })

    assert response.status_code == 200
    body = response.json()
    assert body["metadata"]["query_type"] == "NEW_ISSUE"
    assert body["metadata"]["retrieval_performed"] is True
    assert "sufficient verified information" in body["answer"]
