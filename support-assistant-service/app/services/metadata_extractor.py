import re


class MetadataExtractionService:
    def extract(self, message: str, context: dict[str, str] | None) -> dict[str, str]:
        result = {key: value for key, value in (context or {}).items() if value}
        lowered = message.lower()
        if "production" in lowered:
            result.setdefault("environment", "production")
        match = re.search(r"\b(?:http\s*)?(\d{3})\b", lowered)
        if match:
            result.setdefault("error_code", f"HTTP_{match.group(1)}")
        return result
