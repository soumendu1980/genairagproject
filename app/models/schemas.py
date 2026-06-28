from pydantic import BaseModel, Field


class SourceChunk(BaseModel):
    source: str
    chunk_id: str
    score: float | None = None
    page: int | None = None
    text: str = Field(default='', max_length=1500)


class AnswerItem(BaseModel):
    question: str
    answer: str
    sources: list[SourceChunk] = []
    used_agent: bool = False
    guardrail_notes: list[str] = []


class QueryJsonRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=8000)
    top_k: int = Field(default=5, ge=1, le=20)
    prompt: str | None = Field(default=None, max_length=12000)


class QueryResponse(BaseModel):
    results: list[AnswerItem]


class UploadResponse(BaseModel):
    saved_files: list[str]
    ingested_files: list[str]
    chunks_indexed: int
    errors: list[str] = []


class HealthResponse(BaseModel):
    api: str
    doc_dir: str
    chroma: str
    collection: str
    document_count: int
    vector_count: int
    agent: str
    embedding_model: str
