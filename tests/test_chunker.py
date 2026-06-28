from app.services.document_loader import LoadedDocument
from app.services.chunker import Chunker


def test_chunker_creates_nodes():
    text = ' '.join(['hello world'] * 300)
    nodes = Chunker().build_nodes([LoadedDocument(text=text, metadata={'source': 'unit.txt'})])
    assert len(nodes) >= 1
    assert nodes[0].metadata['source'] == 'unit.txt'
