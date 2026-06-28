import logging
from functools import lru_cache
from typing import Iterable

import chromadb
from llama_index.core import Settings as LlamaSettings
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.schema import TextNode
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from app.core.config import get_settings
from app.models.schemas import SourceChunk

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Chroma-backed LlamaIndex vector store."""

    def __init__(self) -> None:
        settings = get_settings()
        settings.ensure_directories()
        self.settings = settings
        self.client = chromadb.PersistentClient(path=str(settings.chroma_path))
        self.collection = self.client.get_or_create_collection(name=settings.chroma_collection)
        self.embed_model = HuggingFaceEmbedding(model_name=settings.embedding_model_name)
        LlamaSettings.embed_model = self.embed_model
        self.vector_store = ChromaVectorStore(chroma_collection=self.collection)
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)

    def get_index(self) -> VectorStoreIndex:
        return VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store,
            embed_model=self.embed_model,
        )

    def add_nodes(self, nodes: Iterable[TextNode]) -> int:
        node_list = list(nodes)
        if not node_list:
            return 0
        VectorStoreIndex(
            node_list,
            storage_context=self.storage_context,
            embed_model=self.embed_model,
        )
        logger.info('Indexed %s chunks into Chroma collection %s', len(node_list), self.settings.chroma_collection)
        return len(node_list)

    def retrieve(self, query: str, top_k: int | None = None) -> list[SourceChunk]:
        top_k = top_k or self.settings.similarity_top_k
        index = self.get_index()
        retriever = index.as_retriever(similarity_top_k=top_k)
        nodes = retriever.retrieve(query)
        chunks: list[SourceChunk] = []
        for item in nodes:
            node = item.node
            metadata = dict(node.metadata or {})
            chunks.append(
                SourceChunk(
                    source=str(metadata.get('source', 'unknown')),
                    chunk_id=str(node.node_id),
                    score=float(item.score) if item.score is not None else None,
                    page=metadata.get('page'),
                    text=node.get_content(metadata_mode='none')[:1500],
                )
            )
        return chunks

    def count(self) -> int:
        return int(self.collection.count())


@lru_cache
def get_vector_store() -> VectorStoreService:
    return VectorStoreService()
