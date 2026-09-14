class RetrievalDecisionService:
    def requires_retrieval(self, query_type: str, active_evidence: list[dict], message: str) -> bool:
        return self.decide(query_type, active_evidence, message)[0]

    def decide(self, query_type: str, active_evidence: list[dict], message: str) -> tuple[bool, str]:
        if query_type in {"GREETING", "SUMMARY_REQUEST", "CLARIFICATION"}:
            return False, "query_type_does_not_require_knowledge_base"
        if query_type == "FOLLOW_UP" and active_evidence:
            matching_terms = [token for token in ("version", "prevent", "different", "also") if token in message.lower()]
            if matching_terms:
                return True, f"follow_up_introduces_new_entity_terms:{','.join(matching_terms)}"
            return False, "follow_up_uses_active_evidence"
        return True, "new_issue_or_knowledge_query"
