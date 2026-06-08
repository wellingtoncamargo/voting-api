import logging
from dataclasses import dataclass

from app.domain.entities.models import Sessao
from app.domain.exceptions.exceptions import PautaNaoEncontradaError
from app.infrastructure.repositories.pauta_repository import PautaRepository
from app.infrastructure.repositories.sessao_repository import SessaoRepository

logger = logging.getLogger(__name__)


@dataclass
class PaginatedSessoes:
    items: list[Sessao]
    total: int
    page: int
    limit: int


class ListarSessoesUseCase:
    def __init__(self, pauta_repo: PautaRepository, sessao_repo: SessaoRepository):
        self._pauta_repo = pauta_repo
        self._sessao_repo = sessao_repo

    async def executar(self, pauta_id: str, page: int = 1, limit: int = 20) -> PaginatedSessoes:
        pauta = await self._pauta_repo.buscar_por_id(pauta_id)
        if not pauta:
            raise PautaNaoEncontradaError(f"Pauta {pauta_id} não encontrada.")

        skip = (page - 1) * limit
        items = await self._sessao_repo.listar_por_pauta(pauta_id, skip=skip, limit=limit)
        total = await self._sessao_repo.contar_por_pauta(pauta_id)
        logger.info("Sessões listadas.", extra={"event": "sessoes_listed", "pauta_id": pauta_id})
        return PaginatedSessoes(items=items, total=total, page=page, limit=limit)
