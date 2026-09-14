from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import documents, jobs, s3, sync
from app.exceptions.errors import KnowledgeProcessingError

app = FastAPI(title="Support Knowledge Ingestion", version="0.1.0")
app.include_router(documents.router, prefix="/api/v1/knowledge")
app.include_router(s3.router, prefix="/api/v1/knowledge")
app.include_router(jobs.router, prefix="/api/v1/knowledge")
app.include_router(sync.router, prefix="/api/v1/knowledge")


@app.exception_handler(KnowledgeProcessingError)
async def processing_error_handler(_: Request, error: KnowledgeProcessingError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"error": {"code": error.code, "message": str(error)}})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
