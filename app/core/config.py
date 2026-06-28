from functools import lru_cache
from pathlib import Path
from typing import Set

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class AppSettings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = Field(default='RAG Capstone Agent', alias='APP_NAME')
    app_env: str = Field(default='local', alias='APP_ENV')
    app_host: str = Field(default='0.0.0.0', alias='APP_HOST')
    app_port: int = Field(default=8000, alias='APP_PORT')

    doc_dir: Path = Field(default=Path('doc'), alias='DOC_DIR')
    chroma_path: Path = Field(default=Path('data/vector_db'), alias='CHROMA_PATH')
    chroma_collection: str = Field(default='rag_capstone_docs', alias='CHROMA_COLLECTION')

    max_upload_size_mb: int = Field(default=20, alias='MAX_UPLOAD_SIZE_MB')
    chunk_size_tokens: int = Field(default=200, alias='CHUNK_SIZE_TOKENS')
    chunk_overlap_tokens: int = Field(default=30, alias='CHUNK_OVERLAP_TOKENS')
    similarity_top_k: int = Field(default=5, alias='SIMILARITY_TOP_K')

    embedding_model_name: str = Field(
        default='sentence-transformers/all-MiniLM-L6-v2',
        alias='EMBEDDING_MODEL_NAME',
    )
    openai_api_key: str | None = Field(default=None, alias='OPENAI_API_KEY')
    llm_model: str = Field(default='gpt-4o-mini', alias='LLM_MODEL')

    agent_verbose: bool = Field(default=False, alias='AGENT_VERBOSE')
    agent_max_iterations: int = Field(default=8, alias='AGENT_MAX_ITERATIONS')
    log_level: str = Field(default='INFO', alias='LOG_LEVEL')

    allowed_extensions: Set[str] = {
        '.pdf', '.txt', '.md', '.csv', '.xlsx', '.xls', '.json', '.yaml', '.yml', '.docx'
    }

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    def ensure_directories(self) -> None:
        self.doc_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_path.mkdir(parents=True, exist_ok=True)
        Path('logs').mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> AppSettings:
    settings = AppSettings()
    settings.ensure_directories()
    return settings
