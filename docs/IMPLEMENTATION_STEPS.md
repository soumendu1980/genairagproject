# Step-by-Step Implementation

1. Install Python 3.11.
2. Create the virtual environment: `python -m venv .venv`.
3. Activate it: `. .venv/bin/activate` on macOS/Linux or `.venv\Scripts\activate` on Windows.
4. Install dependencies: `pip install -r requirements.txt`.
5. Copy `.env.example` to `.env`.
6. Optional: set `OPENAI_API_KEY` and `LLM_MODEL` for the LlamaIndex ReActAgent.
7. Add documents to `doc/`, or upload them through `/upload-ui`.
8. Ingest documents with `python scripts/ingest_folder.py --folder doc` or through the UI.
9. Start the app: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`.
10. Open `http://127.0.0.1:8000/` and ask questions.
11. Check `http://127.0.0.1:8000/health-ui` for vector counts and agent status.
12. Review API documentation at `http://127.0.0.1:8000/docs`.

## Data ingestion implementation

| Format | Parser |
| --- | --- |
| PDF | `PyPDF2.PdfReader` |
| TXT/MD | Python file read |
| CSV | `pandas.read_csv()` |
| Excel | `pandas.read_excel()` with `openpyxl` |
| JSON | Python `json` |
| YAML | `PyYAML` |
| DOCX | `python-docx` |

## Semantic search implementation

- Split documents into chunks around 200 tokens.
- Add overlap to reduce boundary loss.
- Prefer sentence and paragraph boundaries.
- Embed chunks with the configured HuggingFace embedding model.
- Store vectors, text, and metadata in Chroma.
- Retrieve top-k chunks for each question.

## RAG response implementation

- Validate question.
- Treat user prompt file as untrusted content.
- Retrieve chunks from Chroma.
- Use LLM generation when configured.
- Use extractive fallback when no LLM key exists.
- Verify output against retrieval state.
