import logging
from dataclasses import dataclass

from app.domain.entities.models import Pauta
from app.infrastructure.repositories.pauta_repository import PautaRepository

logger = logging.getLogger(__name__)


@dataclass
class PaginatedPautas:
    items: list[Pauta]
    total: int
    page: int
    limit: int


class ListarPautasUseCase:
    def __init__(self, repo: PautaRepository):
        self._repo = repo

    async def executar(self, page: int = 1, limit: int = 20) -> PaginatedPautas:
        skip = (page - 1) * limit
        items = await self._repo.listar(skip=skip, limit=limit)
        total = await self._repo.contar()
        logger.info("Pautas listadas.", extra={"event": "pautas_listed", "total": total})
        return PaginatedPautas(items=items, total=total, page=page, limit=limit)
