import re
import unicodedata


class Normalizer:
    def normalize(self, content: str) -> str:
        content = unicodedata.normalize("NFKC", content).replace("\r\n", "\n").replace("\r", "\n")
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in content.split("\n")]
        return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
