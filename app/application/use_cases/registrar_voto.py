import logging
from datetime import datetime, timezone

from app.domain.entities.models import StatusSessao, Voto, VotoEnum
from app.domain.exceptions.exceptions import (
    AssociadoNaoEncontradoError,
    SessaoEncerradaError,
    SessaoNaoEncontradaError,
    VotoDuplicadoError,
)
from app.infrastructure.repositories.associado_repository import AssociadoRepository
from app.infrastructure.repositories.sessao_repository import SessaoRepository
from app.infrastructure.repositories.voto_repository import VotoRepository

logger = logging.getLogger(__name__)


class RegistrarVotoUseCase:
    def __init__(
        self,
        sessao_repo: SessaoRepository,
        voto_repo: VotoRepository,
        associado_repo: AssociadoRepository,
    ):
        self._sessao_repo = sessao_repo
        self._voto_repo = voto_repo
        self._associado_repo = associado_repo

    async def executar(self, sessao_id: str, associado_id: str, voto: VotoEnum) -> Voto:
        associado = await self._associado_repo.buscar_por_id(associado_id)
        if not associado:
            raise AssociadoNaoEncontradoError(f"Associado {associado_id} não cadastrado.")

        sessao = await self._sessao_repo.buscar_por_id(sessao_id)
        if not sessao:
            raise SessaoNaoEncontradaError(f"Sessão {sessao_id} não encontrada.")

        agora = datetime.now(tz=timezone.utc).replace(tzinfo=None)
        if sessao.status == StatusSessao.CLOSED or sessao.fim <= agora:
            raise SessaoEncerradaError(f"Sessão {sessao_id} está encerrada.")

        voto_existente = await self._voto_repo.buscar_voto_associado_na_sessao(sessao_id, associado_id)
        if voto_existente:
            raise VotoDuplicadoError(f"Associado {associado_id} já votou nesta sessão.")

        novo_voto = Voto.model_construct(sessao_id=sessao_id, associado_id=associado_id, voto=voto)
        novo_voto = await self._voto_repo.criar(novo_voto)

        logger.info(
            "Voto registrado.",
            extra={"event": "vote_registered", "sessao_id": sessao_id, "associado_id": associado_id},
        )
        return novo_voto
