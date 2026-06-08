import logging
from typing import Optional

from app.domain.entities.models import Pauta
from app.domain.exceptions.exceptions import PautaNaoEncontradaError, PautaNaoAtualizadaError
from app.infrastructure.repositories.pauta_repository import PautaRepository

logger = logging.getLogger(__name__)


class AtualizarPautaUseCase:
    def __init__(self, repo: PautaRepository):
        self._repo = repo

    async def executar(self, pauta_id: str, titulo: Optional[str], descricao: Optional[str]) -> Pauta:
        if titulo is None and descricao is None:
            raise PautaNaoAtualizadaError("Pelo menos um campo deve ser informado para atualização.")

        pauta = await self._repo.buscar_por_id(pauta_id)
        if not pauta:
            raise PautaNaoEncontradaError(f"Pauta {pauta_id} não encontrada.")

        pauta = await self._repo.atualizar(pauta, titulo=titulo, descricao=descricao)
        logger.info("Pauta atualizada.", extra={"event": "pauta_updated", "pauta_id": pauta_id})
        return pauta
