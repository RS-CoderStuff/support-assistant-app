import fitz

from app.exceptions.errors import ParserError
from app.models.document import ParseContext, ParsedDocument
from app.parsers.base import DocumentParser, parsed, with_file_classification


class PDFParser(DocumentParser):
    def supports(self, file_name: str, content_type: str | None) -> bool:
        return file_name.lower().endswith(".pdf") or content_type == "application/pdf"

    def parse(self, source: bytes, context: ParseContext) -> list[ParsedDocument]:
        context = with_file_classification(context, "pdf")
        try:
            pdf = fitz.open(stream=source, filetype="pdf")
            pages = [f"PAGE {index + 1}:\n{page.get_text().strip()}" for index, page in enumerate(pdf) if page.get_text().strip()]
            title = str(pdf.metadata.get("title") or context.file_name)
            pdf.close()
        except Exception as error:
            raise ParserError("Unable to parse PDF") from error
        return [parsed(context, title, "\n\n".join(pages), {"page_count": len(pages)})]
