# from contextlib import asynccontextmanager
# from fastapi import FastAPI
# from app.core.config import settings
# from app.core.logging_config import setup_logging
# from app.core.scheduler import start_scheduler, stop_scheduler
# from app.core.exception_handlers import register_exception_handlers
# from app.infrastructure.database.mongodb import connect_db, close_db
# from app.api.v1.router import router as api_v1_router
#
# setup_logging()
#
#
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     await connect_db()
#     start_scheduler()
#     yield
#     stop_scheduler()
#     await close_db()
#
#
#     app = FastAPI(
#         title=settings.APP_NAME,
#         version=settings.APP_VERSION,
#         description=(
#             "API REST para gerenciamento de pautas e sessões de votação em assembleias cooperativas. "
#             "Desenvolvida com FastAPI, MongoDB e Clean Architecture."
#         ),
#         docs_url="/docs",
#         redoc_url="/redoc",
#         lifespan=lifespan,
#     )
#
#     register_exception_handlers(app)
#     app.include_router(api_v1_router)
#
#
#     @app.get("/health", tags=["Health"], summary="Verificação de saúde da aplicação")
#     async def health_check():
#         return {"status": "ok", "version": settings.APP_VERSION}


from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.scheduler import start_scheduler, stop_scheduler
from app.core.exception_handlers import register_exception_handlers
from app.infrastructure.database.mongodb import connect_db, close_db
from app.api.v1.router import router as api_v1_router

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    start_scheduler()

    yield

    stop_scheduler()
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "API REST para gerenciamento de pautas e sessões de votação "
        "em assembleias cooperativas."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

register_exception_handlers(app)

app.include_router(api_v1_router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )