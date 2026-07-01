import logging

from app.domain.entities.models import Associado, PerfilAssociado
from app.domain.exceptions.exceptions import AssociadoNaoEncontradoError, PermissaoNegadaError
from app.infrastructure.repositories.associado_repository import AssociadoRepository

logger = logging.getLogger(__name__)


class AtualizarPerfilAssociadoUseCase:
    def __init__(self, repo: AssociadoRepository):
        self._repo = repo

    async def executar(
        self,
        associado_id: str,
        role: PerfilAssociado,
        solicitante: Associado,
    ) -> Associado:
        if solicitante.role != PerfilAssociado.ADMIN:
            raise PermissaoNegadaError("Somente administradores podem alterar perfis.")

        associado = await self._repo.buscar_por_id(associado_id)
        if not associado:
            raise AssociadoNaoEncontradoError(f"Associado {associado_id} não encontrado.")

        associado = await self._repo.atualizar_perfil(associado, role)
        logger.info(
            "Perfil do associado atualizado.",
            extra={"event": "associado_role_updated", "associado_id": associado_id, "role": role.value},
        )
        return associado

