import re


class QueryClassifier:
    def classify(self, message: str, has_conversation_context: bool) -> str:
        normalized = message.strip().lower()
        if re.search(r"\b(hello|hi|good morning|good afternoon)\b", normalized):
            return "GREETING"
        summary_references = ("previous", "answer", "whole thing", "everything", "conversation", "discussion", "so far", "we discussed")
        if re.search(r"\b(summarize|summarise|recap)\b", normalized) and any(reference in normalized for reference in summary_references):
            return "SUMMARY_REQUEST"
        if has_conversation_context and re.search(r"\b(this|that|it|previous answer)\b", normalized):
            if "explain" in normalized or "simple" in normalized:
                return "CLARIFICATION"
            return "FOLLOW_UP"
        if re.search(r"\b(error|fail|failure|incident|503|issue|after deployment)\b", normalized):
            return "NEW_ISSUE"
        return "KNOWLEDGE_QUERY"
