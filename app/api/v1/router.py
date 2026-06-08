from fastapi import APIRouter
from app.api.v1.routes import pautas, votos, associados

router = APIRouter(prefix="/api/v1")
router.include_router(pautas.router)
router.include_router(votos.router)
router.include_router(associados.router)
