import re
from enum import StrEnum

from app.exceptions.errors import SanitizationError


class SanitizationMode(StrEnum):
    MASK = "MASK"
    REMOVE = "REMOVE"
    REJECT = "REJECT"


class Sanitizer:
    patterns = (
        re.compile(r"(?im)(password\s*[:=]\s*)([^\s,;]+)"),
        re.compile(r"(?im)(authorization\s*:\s*bearer\s+)([^\s,;]+)"),
        re.compile(r"(?im)(api[_-]?key\s*[:=]\s*)([^\s,;]+)"),
        re.compile(r"(?im)(access[_-]?token\s*[:=]\s*)([^\s,;]+)"),
    )

    def __init__(self, mode: SanitizationMode = SanitizationMode.MASK) -> None:
        self.mode = mode

    def sanitize(self, content: str) -> tuple[str, int]:
        count = sum(len(pattern.findall(content)) for pattern in self.patterns)
        if count and self.mode is SanitizationMode.REJECT:
            raise SanitizationError("Sensitive content detected")
        replacement = "[REDACTED]" if self.mode is SanitizationMode.MASK else ""
        for pattern in self.patterns:
            content = pattern.sub(lambda match: f"{match.group(1)}{replacement}", content)
        return content, count
