# API Documentation

## Base URL

Local: `http://127.0.0.1:8000`

OpenAPI UI: `/docs`

## GET /api/v1/health

Returns the health of the API, upload directory, Chroma vector database, vector count, and agent mode.

Example response:

```json
{
  "api": "ok",
  "doc_dir": "ok",
  "chroma": "ok",
  "collection": "rag_capstone_docs",
  "document_count": 3,
  "vector_count": 85,
  "agent": "enabled",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
}
```

## POST /api/v1/upload

Multipart form fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `files` | file[] | yes | Documents to save under `doc/` |
| `ingest` | bool | no | When true, index immediately into Chroma |

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/upload \
  -F "ingest=true" \
  -F "files=@sample.pdf"
```

## POST /api/v1/ingest-local

Ingests every supported file already located under the `doc/` folder.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/ingest-local
```

## POST /api/v1/query

Multipart form fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `question` | string | no | One natural-language question |
| `top_k` | int | no | Number of retrieved chunks, 1 to 20 |
| `prompt_file` | file | no | Natural-language prompt file; treated as untrusted |
| `question_file` | file | no | TXT lines, CSV with `question` column, or JSON list |
| `documents` | file[] | no | Documents to upload and ingest before answering |

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/query \
  -F "question=What are the security considerations?" \
  -F "top_k=5"
```

## POST /api/v1/query-json

JSON body:

```json
{
  "question": "What formats are supported?",
  "top_k": 5,
  "prompt": "Answer in concise bullet points."
}
```

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/query-json \
  -H "Content-Type: application/json" \
  -d '{"question":"What formats are supported?","top_k":5}'
```

## GET /api/v1/search

Returns raw retrieved chunks without answer generation.

```bash
curl "http://127.0.0.1:8000/api/v1/search?question=semantic%20search&top_k=3"
```

## GET /api/v1/documents

Lists files saved under `doc/`.
