import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.domain.entities.models import Sessao, StatusSessao
from app.domain.exceptions.exceptions import PautaNaoEncontradaError, SessaoJaAtivaError
from app.infrastructure.repositories.pauta_repository import PautaRepository
from app.infrastructure.repositories.sessao_repository import SessaoRepository

logger = logging.getLogger(__name__)

DURACAO_PADRAO_SEGUNDOS = 60


class AbrirSessaoUseCase:
    def __init__(self, pauta_repo: PautaRepository, sessao_repo: SessaoRepository):
        self._pauta_repo = pauta_repo
        self._sessao_repo = sessao_repo

    async def executar(self, pauta_id: str, duracao_segundos: Optional[int]) -> Sessao:
        pauta = await self._pauta_repo.buscar_por_id(pauta_id)
        if not pauta:
            raise PautaNaoEncontradaError(f"Pauta {pauta_id} não encontrada.")

        sessao_ativa = await self._sessao_repo.buscar_sessao_ativa_por_pauta(pauta_id)
        if sessao_ativa:
            raise SessaoJaAtivaError(f"A pauta {pauta_id} já possui uma sessão ativa.")

        duracao = duracao_segundos or DURACAO_PADRAO_SEGUNDOS
        inicio = datetime.now(tz=timezone.utc).replace(tzinfo=None)
        fim = inicio + timedelta(seconds=duracao)

        sessao = Sessao.model_construct(
            pauta_id=pauta_id,
            inicio=inicio,
            fim=fim,
            status=StatusSessao.OPEN,
        )
        sessao = await self._sessao_repo.criar(sessao)

        logger.info(
            "Sessão aberta.",
            extra={
                "event": "session_opened",
                "sessao_id": sessao.id,
                "pauta_id": pauta_id,
                "duracao_segundos": duracao,
            },
        )
        return sessao
