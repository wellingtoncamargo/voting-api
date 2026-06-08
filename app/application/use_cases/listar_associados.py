import logging
from dataclasses import dataclass

from app.domain.entities.models import Associado
from app.infrastructure.repositories.associado_repository import AssociadoRepository

logger = logging.getLogger(__name__)


@dataclass
class PaginatedAssociados:
    items: list[Associado]
    total: int
    page: int
    limit: int


class ListarAssociadosUseCase:
    def __init__(self, repo: AssociadoRepository):
        self._repo = repo

    async def executar(self, page: int = 1, limit: int = 20) -> PaginatedAssociados:
        skip = (page - 1) * limit
        items = await self._repo.listar(skip=skip, limit=limit)
        total = await self._repo.contar()
        logger.info("Associados listados.", extra={"event": "associados_listed", "total": total})
        return PaginatedAssociados(items=items, total=total, page=page, limit=limit)
