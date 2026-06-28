import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version='1.0.0',
    description='FastAPI + LlamaIndex + Chroma RAG capstone project with a ReAct agent.',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'] if settings.app_env == 'local' else [],
    allow_credentials=False,
    allow_methods=['GET', 'POST'],
    allow_headers=['*'],
)

app.mount('/static', StaticFiles(directory='app/static'), name='static')
app.include_router(router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception('Unhandled error for %s: %s', request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={'detail': 'Unexpected server error. Check logs/app.log for details.'},
    )


@app.on_event('startup')
async def startup_event():
    settings.ensure_directories()
    logger.info('%s started in %s mode', settings.app_name, settings.app_env)
