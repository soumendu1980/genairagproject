# Limitations and Security Considerations

## Limitations

1. OCR is not implemented; scanned PDFs may produce little or no text.
2. Local Chroma is best for capstone, demos, and small workloads; production should use durable storage.
3. The default local embedding model has startup download cost.
4. The prompt-injection guardrail is pattern-based and should be enhanced for production.
5. The fallback answer mode is extractive and may be less fluent than LLM synthesis.
6. Uploaded documents are not virus-scanned by default.
7. Authentication and role-based access control are not enabled by default.
8. Render free or ephemeral environments may not preserve `data/vector_db` after redeploys unless persistent disk is configured.

## Security controls included

| Control | Implementation |
| --- | --- |
| File extension allowlist | `app/core/security.py` |
| File size limit | `MAX_UPLOAD_SIZE_MB` |
| Path traversal prevention | Sanitized basename filenames |
| Prompt-injection filter | Pattern checks for known jailbreak phrases |
| Grounded-answer rule | Agent and RAG prompts require context-only responses |
| No-source fallback | Returns "I do not know based on the uploaded documents" |
| Secret management | `.env` and Render secret environment variables |
| Logging | Rotating log file under `logs/app.log` |

## Recommended production hardening

- Add login and role-based access control.
- Add per-user document namespaces or collections.
- Add malware scanning before ingestion.
- Add rate limiting per IP/user.
- Add HTTPS-only deployment and secure headers.
- Add persistent disk or a managed vector database.
- Add observability metrics, tracing, and alerting.
- Add document retention policies and deletion endpoints.
- Add automated RAG evaluation tests.
