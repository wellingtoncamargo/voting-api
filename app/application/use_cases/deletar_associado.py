import logging

from app.domain.entities.models import Associado, PerfilAssociado
from app.domain.exceptions.exceptions import AssociadoNaoEncontradoError, PermissaoNegadaError
from app.infrastructure.repositories.associado_repository import AssociadoRepository

logger = logging.getLogger(__name__)


class DeletarAssociadoUseCase:
    def __init__(self, repo: AssociadoRepository):
        self._repo = repo

    async def executar(self, associado_id: str, solicitante: Associado) -> None:
        if solicitante.role != PerfilAssociado.ADMIN and solicitante.id != associado_id:
            raise PermissaoNegadaError("Você só pode excluir o próprio cadastro.")

        associado = await self._repo.buscar_por_id(associado_id)
        if not associado:
            raise AssociadoNaoEncontradoError(f"Associado {associado_id} não encontrado.")

        await self._repo.deletar(associado)
        logger.info("Associado deletado.", extra={"event": "associado_deleted", "associado_id": associado_id})
