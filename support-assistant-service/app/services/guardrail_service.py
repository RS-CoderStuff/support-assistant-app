import re

from app.exceptions.exceptions import GuardrailException


class InputGuardrail:
    def validate(self, message: str) -> None:
        if re.search(r"reveal (the )?(system prompt|secrets)|ignore all previous instructions", message, re.IGNORECASE):
            raise GuardrailException()


class OutputGuardrail:
    def validate(self, answer: str) -> str:
        return answer
