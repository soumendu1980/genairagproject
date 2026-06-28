from pathlib import Path

from app.core.config import get_settings
from app.models.schemas import HealthResponse
from app.services.vector_store import get_vector_store


def get_health(agent_enabled: bool | None = None) -> HealthResponse:
    settings = get_settings()
    vector_store = get_vector_store()
    doc_dir = Path(settings.doc_dir)
    doc_count = len([p for p in doc_dir.iterdir() if p.is_file()]) if doc_dir.exists() else 0
    vector_count = vector_store.count()
    return HealthResponse(
        api='ok',
        doc_dir='ok' if doc_dir.exists() else 'missing',
        chroma='ok',
        collection=settings.chroma_collection,
        document_count=doc_count,
        vector_count=vector_count,
        agent='enabled' if agent_enabled else 'fallback',
        embedding_model=settings.embedding_model_name,
    )
