import logging
from dataclasses import dataclass

from app.domain.entities.models import Voto
from app.domain.exceptions.exceptions import SessaoNaoEncontradaError
from app.infrastructure.repositories.sessao_repository import SessaoRepository
from app.infrastructure.repositories.voto_repository import VotoRepository

logger = logging.getLogger(__name__)


@dataclass
class PaginatedVotos:
    items: list[Voto]
    total: int
    page: int
    limit: int


class ListarVotosUseCase:
    def __init__(self, sessao_repo: SessaoRepository, voto_repo: VotoRepository):
        self._sessao_repo = sessao_repo
        self._voto_repo = voto_repo

    async def executar(self, sessao_id: str, page: int = 1, limit: int = 50) -> PaginatedVotos:
        sessao = await self._sessao_repo.buscar_por_id(sessao_id)
        if not sessao:
            raise SessaoNaoEncontradaError(f"Sessão {sessao_id} não encontrada.")

        skip = (page - 1) * limit
        items = await self._voto_repo.listar_por_sessao(sessao_id, skip=skip, limit=limit)
        total = await self._voto_repo.contar_por_sessao(sessao_id)
        logger.info("Votos listados.", extra={"event": "votos_listed", "sessao_id": sessao_id})
        return PaginatedVotos(items=items, total=total, page=page, limit=limit)
