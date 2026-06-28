# Render Deployment Guide

## Files used

- `requirements.txt`: Python dependencies.
- `render.yaml`: Render Blueprint service definition.
- `.env.example`: local environment template.
- `Dockerfile`: optional container deployment.

## Blueprint deployment steps

1. Push the project folder to a Git repository.
2. In Render, create a new Blueprint and select the repository.
3. Confirm Render detects `render.yaml` in the repository root.
4. Add `OPENAI_API_KEY` as a secret environment variable in the Render dashboard.
5. Deploy the web service.
6. Open the generated Render URL.
7. Visit `/health-ui` to confirm the API starts and Chroma is reachable.
8. Upload and ingest a small document from `/upload-ui`.
9. Ask a test question from `/`.

## Important Render notes

- The app start command is `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- Secret values should not be committed into `render.yaml`.
- For durable vectors, configure persistent disk or use external Chroma/server-backed vector storage.
- The first startup may take longer while the embedding model downloads.

## Manual Render web service setup

If not using Blueprint:

- Runtime: Python.
- Build command: `pip install --upgrade pip && pip install -r requirements.txt`.
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- Environment variables: use values from `.env.example`, especially `OPENAI_API_KEY`, `CHROMA_PATH`, `DOC_DIR`, and `EMBEDDING_MODEL_NAME`.
