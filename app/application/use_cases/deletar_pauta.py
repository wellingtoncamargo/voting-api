import logging

from app.domain.exceptions.exceptions import PautaNaoEncontradaError, SessaoJaAtivaError
from app.infrastructure.repositories.pauta_repository import PautaRepository
from app.infrastructure.repositories.sessao_repository import SessaoRepository

logger = logging.getLogger(__name__)


class DeletarPautaUseCase:
    def __init__(self, repo: PautaRepository, sessao_repo: SessaoRepository):
        self._repo = repo
        self._sessao_repo = sessao_repo

    async def executar(self, pauta_id: str) -> None:
        pauta = await self._repo.buscar_por_id(pauta_id)
        if not pauta:
            raise PautaNaoEncontradaError(f"Pauta {pauta_id} não encontrada.")

        sessao_ativa = await self._sessao_repo.buscar_sessao_ativa_por_pauta(pauta_id)
        if sessao_ativa:
            raise SessaoJaAtivaError(
                f"Pauta {pauta_id} possui sessão ativa e não pode ser removida."
            )

        await self._repo.deletar(pauta)
        logger.info("Pauta deletada.", extra={"event": "pauta_deleted", "pauta_id": pauta_id})
