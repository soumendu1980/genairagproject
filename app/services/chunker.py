import hashlib
from typing import Iterable

from llama_index.core import Document as LlamaDocument
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import TextNode

from app.core.config import get_settings
from app.services.document_loader import LoadedDocument


def _stable_id(text: str, source: str, index: int) -> str:
    digest = hashlib.sha256(f'{source}:{index}:{text}'.encode('utf-8')).hexdigest()[:16]
    return f'{source}:{index}:{digest}'


class Chunker:
    """Chunk text into about 200 tokens with overlap and sentence boundaries."""

    def __init__(self) -> None:
        settings = get_settings()
        self.chunk_size = settings.chunk_size_tokens
        self.chunk_overlap = settings.chunk_overlap_tokens
        self.splitter = SentenceSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            paragraph_separator='\n\n',
        )

    def build_nodes(self, documents: Iterable[LoadedDocument]) -> list[TextNode]:
        llama_docs = [
            LlamaDocument(text=doc.text, metadata=doc.metadata)
            for doc in documents
            if doc.text and doc.text.strip()
        ]
        nodes = self.splitter.get_nodes_from_documents(llama_docs)
        for i, node in enumerate(nodes):
            source = str(node.metadata.get('source', 'unknown'))
            node.id_ = _stable_id(node.get_content(metadata_mode='none'), source, i)
        return nodes
