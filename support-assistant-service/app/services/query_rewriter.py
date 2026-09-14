class QueryRewriteService:
    def rewrite(self, message: str, current_issue: dict[str, str]) -> str:
        if not current_issue:
            return message
        lower_message = message.lower()
        if not any(reference in lower_message for reference in ("this", "that", "it")):
            return message
        issue = " ".join(str(value) for value in current_issue.values() if value)
        return f"{message.rstrip('?')} regarding {issue}?"
