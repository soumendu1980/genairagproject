import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings


DANGEROUS_PROMPT_PATTERNS = [
    r'ignore\s+(all\s+)?(previous|prior)\s+instructions',
    r'reveal\s+(the\s+)?(system|developer)\s+prompt',
    r'exfiltrate|steal|leak\s+(secrets?|api\s*keys?|tokens?)',
    r'disregard\s+(the\s+)?(policy|guardrails|safety)',
    r'jailbreak|do\s+anything\s+now',
]


@dataclass(frozen=True)
class GuardrailResult:
    allowed: bool
    reason: str = ''


def safe_filename(filename: str) -> str:
    """Return a path-safe filename while preserving the extension."""
    original = Path(filename or 'uploaded_file').name
    stem = Path(original).stem
    suffix = Path(original).suffix.lower()
    stem = re.sub(r'[^A-Za-z0-9_.-]+', '_', stem).strip('._') or 'uploaded_file'
    return f'{stem}{suffix}'


def file_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def validate_file_name(filename: str) -> None:
    settings = get_settings()
    suffix = Path(filename or '').suffix.lower()
    if suffix not in settings.allowed_extensions:
        allowed = ', '.join(sorted(settings.allowed_extensions))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Unsupported file type {suffix!r}. Allowed extensions: {allowed}',
        )


def validate_file_bytes(filename: str, content: bytes) -> None:
    settings = get_settings()
    validate_file_name(filename)
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Uploaded file is empty.')
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f'File exceeds {settings.max_upload_size_mb} MB limit.',
        )


async def save_upload_file(upload: UploadFile, destination_dir: Path) -> Path:
    """Validate and save a FastAPI UploadFile into the doc directory."""
    content = await upload.read()
    validate_file_bytes(upload.filename or 'uploaded_file', content)
    destination_dir.mkdir(parents=True, exist_ok=True)
    safe_name = safe_filename(upload.filename or 'uploaded_file')
    digest = file_sha256(content)[:12]
    target = destination_dir / f'{Path(safe_name).stem}_{digest}{Path(safe_name).suffix.lower()}'
    target.write_bytes(content)
    return target


def validate_question(question: str) -> GuardrailResult:
    question = (question or '').strip()
    if not question:
        return GuardrailResult(False, 'Question is required.')
    if len(question) > 8000:
        return GuardrailResult(False, 'Question is too long. Keep it under 8,000 characters.')
    return GuardrailResult(True)


def validate_untrusted_prompt(prompt: str | None) -> GuardrailResult:
    prompt = (prompt or '').strip()
    if not prompt:
        return GuardrailResult(True)
    if len(prompt) > 12000:
        return GuardrailResult(False, 'Prompt file is too long. Keep it under 12,000 characters.')
    lower = prompt.lower()
    for pattern in DANGEROUS_PROMPT_PATTERNS:
        if re.search(pattern, lower, flags=re.IGNORECASE):
            return GuardrailResult(False, f'Prompt failed guardrail pattern: {pattern}')
    return GuardrailResult(True)


def sanitize_text(text: str) -> str:
    """Basic text cleanup for extracted document content."""
    text = text.replace('\x00', ' ')
    text = re.sub(r'[\t\r\f\v]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ ]{2,}', ' ', text)
    return text.strip()


def output_has_sources(answer: str, source_ids: Iterable[str]) -> GuardrailResult:
    source_ids = list(source_ids)
    if not source_ids:
        if 'uploaded documents' in answer.lower() or "don't know" in answer.lower() or 'do not know' in answer.lower():
            return GuardrailResult(True)
        return GuardrailResult(False, 'Output contains an answer even though retrieval returned no sources.')
    if len(answer.strip()) < 3:
        return GuardrailResult(False, 'Output is empty.')
    return GuardrailResult(True)
