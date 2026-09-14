class ApplicationException(Exception):
    status_code = 500
    public_message = "An unexpected service error occurred."


class ConversationNotFoundException(ApplicationException):
    status_code = 404
    public_message = "Conversation not found."


class ConversationPersistenceException(ApplicationException):
    status_code = 503
    public_message = "Conversation state is temporarily unavailable."


class KnowledgeBaseRetrievalException(ApplicationException):
    status_code = 503
    public_message = "Support knowledge retrieval is temporarily unavailable."


class RerankingException(KnowledgeBaseRetrievalException):
    pass


class LLMInvocationException(ApplicationException):
    status_code = 503
    public_message = "Answer generation is temporarily unavailable."


class GuardrailException(ApplicationException):
    status_code = 400
    public_message = "This request cannot be processed."
