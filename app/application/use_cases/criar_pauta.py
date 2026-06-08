import logging
from typing import Optional

from app.domain.entities.models import Pauta
from app.infrastructure.repositories.pauta_repository import PautaRepository

logger = logging.getLogger(__name__)


class CriarPautaUseCase:
    def __init__(self, repo: PautaRepository):
        self._repo = repo

    async def executar(self, titulo: str, descricao: Optional[str]) -> Pauta:
        pauta = Pauta.model_construct(titulo=titulo, descricao=descricao)
        pauta = await self._repo.criar(pauta)
        logger.info("Pauta criada.", extra={"event": "pauta_created", "pauta_id": pauta.id})
        return pauta
