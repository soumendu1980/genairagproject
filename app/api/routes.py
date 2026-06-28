import asyncio
import json
from pathlib import Path
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import get_settings
from app.core.security import save_upload_file, sanitize_text
from app.models.schemas import QueryJsonRequest, QueryResponse, UploadResponse
from app.services.agent import RAGReActAgent
from app.services.health import get_health
from app.services.rag_pipeline import RAGPipeline

router = APIRouter()
templates = Jinja2Templates(directory='app/templates')
settings = get_settings()


def _agent() -> RAGReActAgent:
    return RAGReActAgent()


def _rag() -> RAGPipeline:
    return RAGPipeline()

async def _save_many(files: list[UploadFile] | None) -> list[Path]:
    saved: list[Path] = []
    for upload in files or []:
        if not upload.filename:
            continue
        saved.append(await save_upload_file(upload, settings.doc_dir))
    return saved


async def _read_optional_text(upload: UploadFile | None) -> str | None:
    if not upload or not upload.filename:
        return None
    content = await upload.read()
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail='Prompt or question file is too large.')
    return content.decode('utf-8', errors='ignore')


def _questions_from_text(text: str | None) -> list[str]:
    if not text:
        return []
    text = text.strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [str(x).strip() for x in parsed if str(x).strip()]
        if isinstance(parsed, dict) and isinstance(parsed.get('questions'), list):
            return [str(x).strip() for x in parsed['questions'] if str(x).strip()]
    except Exception:
        pass
    return [line.strip(' -\t') for line in text.splitlines() if line.strip(' -\t')]


def _questions_from_dataframe(text: str) -> list[str]:
    try:
        from io import StringIO
        frame = pd.read_csv(StringIO(text))
        if 'question' in frame.columns:
            return [str(q).strip() for q in frame['question'].dropna().tolist() if str(q).strip()]
    except Exception:
        return []
    return []


@router.get('/', response_class=HTMLResponse, tags=['UI'])
async def query_screen(request: Request):
    return templates.TemplateResponse('query.html', {'request': request, 'results': None})


@router.post('/ui/query', response_class=HTMLResponse, tags=['UI'])
async def query_screen_submit(
    request: Request,
    question: Annotated[str | None, Form()] = None,
    top_k: Annotated[int, Form()] = 5,
    prompt_file: Annotated[UploadFile | None, File()] = None,
    question_file: Annotated[UploadFile | None, File()] = None,
    documents: Annotated[list[UploadFile] | None, File()] = None,
):
    saved = await _save_many(documents)
    ingest_message = ''
    if saved:
        chunks, ingested, errors = await asyncio.to_thread(_rag().ingest_paths, saved)
        ingest_message = f'Ingested {len(ingested)} files and {chunks} chunks.'
        if errors:
            ingest_message += ' Errors: ' + '; '.join(errors)
    prompt = await _read_optional_text(prompt_file)
    q_text = await _read_optional_text(question_file)
    questions = []
    questions.extend(_questions_from_dataframe(q_text or ''))
    questions.extend(_questions_from_text(q_text))
    if question and question.strip():
        questions.insert(0, question.strip())
    questions = list(dict.fromkeys([q for q in questions if q]))
    if not questions:
        questions = ['Please provide a question.']
    agent = _agent()
    results = [await asyncio.to_thread(agent.ask, q, top_k, prompt) for q in questions]
    return templates.TemplateResponse('query.html', {'request': request, 'results': results, 'ingest_message': ingest_message})


@router.get('/health-ui', response_class=HTMLResponse, tags=['UI'])
async def health_screen(request: Request):
    agent = _agent()
    health = get_health(agent_enabled=agent.agent is not None)
    return templates.TemplateResponse('health.html', {'request': request, 'health': health})


@router.get('/upload-ui', response_class=HTMLResponse, tags=['UI'])
async def upload_screen(request: Request):
    return templates.TemplateResponse('upload.html', {'request': request, 'result': None})


@router.post('/ui/upload', response_class=HTMLResponse, tags=['UI'])
async def upload_screen_submit(
    request: Request,
    files: Annotated[list[UploadFile], File()],
    ingest: Annotated[bool, Form()] = True,
):
    saved = await _save_many(files)
    chunks = 0
    ingested: list[str] = []
    errors: list[str] = []
    if ingest:
        chunks, ingested, errors = await asyncio.to_thread(_rag().ingest_paths, saved)
    result = UploadResponse(saved_files=[str(p) for p in saved], ingested_files=ingested, chunks_indexed=chunks, errors=errors)
    return templates.TemplateResponse('upload.html', {'request': request, 'result': result})


@router.get('/api/v1/health', tags=['API'])
async def api_health():
    agent = _agent()
    return get_health(agent_enabled=agent.agent is not None)


@router.post('/api/v1/upload', response_model=UploadResponse, tags=['API'])
async def api_upload(
    files: Annotated[list[UploadFile], File(description='Documents to save under doc/')],
    ingest: Annotated[bool, Form(description='When true, immediately index into Chroma')] = True,
):
    saved = await _save_many(files)
    chunks = 0
    ingested: list[str] = []
    errors: list[str] = []
    if ingest:
        chunks, ingested, errors = await asyncio.to_thread(_rag().ingest_paths, saved)
    return UploadResponse(saved_files=[str(p) for p in saved], ingested_files=ingested, chunks_indexed=chunks, errors=errors)


@router.post('/api/v1/ingest-local', response_model=UploadResponse, tags=['API'])
async def api_ingest_local():
    chunks, ingested, errors = await asyncio.to_thread(_rag().ingest_doc_folder)
    return UploadResponse(saved_files=[], ingested_files=ingested, chunks_indexed=chunks, errors=errors)


@router.post('/api/v1/query', response_model=QueryResponse, tags=['API'])
async def api_query_form(
    question: Annotated[str | None, Form()] = None,
    top_k: Annotated[int, Form(ge=1, le=20)] = 5,
    prompt_file: Annotated[UploadFile | None, File()] = None,
    question_file: Annotated[UploadFile | None, File()] = None,
    documents: Annotated[list[UploadFile] | None, File()] = None,
):
    saved = await _save_many(documents)
    if saved:
        await asyncio.to_thread(_rag().ingest_paths, saved)
    prompt = await _read_optional_text(prompt_file)
    question_text = await _read_optional_text(question_file)
    questions = []
    questions.extend(_questions_from_dataframe(question_text or ''))
    questions.extend(_questions_from_text(question_text))
    if question and question.strip():
        questions.insert(0, question.strip())
    questions = list(dict.fromkeys([q for q in questions if q]))
    if not questions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Question or question_file is required.')
    agent = _agent()
    results = [await asyncio.to_thread(agent.ask, q, top_k, prompt) for q in questions]
    return QueryResponse(results=results)


@router.post('/api/v1/query-json', response_model=QueryResponse, tags=['API'])
async def api_query_json(payload: QueryJsonRequest):
    agent = _agent()
    result = await asyncio.to_thread(agent.ask, payload.question, payload.top_k, payload.prompt)
    return QueryResponse(results=[result])


@router.get('/api/v1/search', tags=['API'])
async def api_search(question: str, top_k: int = 5):
    chunks = await asyncio.to_thread(_rag().retrieve, question, top_k)
    return {'question': question, 'chunks': chunks}


@router.get('/api/v1/documents', tags=['API'])
async def list_documents():
    files = []
    for path in sorted(settings.doc_dir.iterdir()):
        if path.is_file():
            files.append({'name': path.name, 'size_bytes': path.stat().st_size, 'path': str(path)})
    return {'documents': files}
