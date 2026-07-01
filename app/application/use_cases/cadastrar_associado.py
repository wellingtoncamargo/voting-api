import logging

from app.core.config import settings
from app.domain.entities.models import Associado, PerfilAssociado
from app.domain.exceptions.exceptions import AssociadoJaCadastradoError
from app.infrastructure.external.voter_validation_client import VoterValidationClient
from app.infrastructure.repositories.associado_repository import AssociadoRepository

logger = logging.getLogger(__name__)


class CadastrarAssociadoUseCase:
    def __init__(self, repo: AssociadoRepository, validator: VoterValidationClient):
        self._repo = repo
        self._validator = validator

    async def executar(self, cpf: str) -> Associado:
        await self._validator.validar_cpf(cpf)

        existente = await self._repo.buscar_por_cpf(cpf)
        if existente:
            raise AssociadoJaCadastradoError(f"CPF {cpf} já cadastrado.")

        role = PerfilAssociado.ADMIN if settings.INITIAL_ADMIN_CPF and cpf == settings.INITIAL_ADMIN_CPF else PerfilAssociado.USER
        associado = Associado.model_construct(cpf=cpf, role=role)
        associado = await self._repo.criar(associado)

        logger.info(
            "Associado cadastrado.",
            extra={"event": "associate_registered", "associado_id": associado.id},
        )
        return associado
