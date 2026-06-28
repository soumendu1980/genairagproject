import argparse
from pathlib import Path

from app.core.config import get_settings
from app.services.rag_pipeline import RAGPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description='Ingest files from a folder into the Chroma RAG index.')
    parser.add_argument('--folder', default=None, help='Folder to ingest. Defaults to DOC_DIR from .env.')
    args = parser.parse_args()

    settings = get_settings()
    folder = Path(args.folder) if args.folder else settings.doc_dir
    paths = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in settings.allowed_extensions]
    count, ingested, errors = RAGPipeline().ingest_paths(paths)
    print(f'Indexed chunks: {count}')
    print('Ingested files:')
    for item in ingested:
        print(f'  - {item}')
    if errors:
        print('Errors:')
        for error in errors:
            print(f'  - {error}')


if __name__ == '__main__':
    main()
