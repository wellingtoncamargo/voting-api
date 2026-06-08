import logging

from app.domain.entities.models import Sessao, StatusSessao
from app.domain.exceptions.exceptions import SessaoNaoEncontradaError, SessaoEncerradaError
from app.infrastructure.repositories.sessao_repository import SessaoRepository
from app.infrastructure.repositories.voto_repository import VotoRepository
from app.infrastructure.messaging.publisher import publicar_resultado_votacao

logger = logging.getLogger(__name__)


class EncerrarSessaoUseCase:
    def __init__(self, sessao_repo: SessaoRepository, voto_repo: VotoRepository):
        self._sessao_repo = sessao_repo
        self._voto_repo = voto_repo

    async def executar(self, sessao_id: str) -> Sessao:
        sessao = await self._sessao_repo.buscar_por_id(sessao_id)
        if not sessao:
            raise SessaoNaoEncontradaError(f"Sessão {sessao_id} não encontrada.")

        if sessao.status == StatusSessao.CLOSED:
            raise SessaoEncerradaError(f"Sessão {sessao_id} já está encerrada.")

        sessao = await self._sessao_repo.atualizar_status(sessao, StatusSessao.CLOSED)

        contagem = await self._voto_repo.contar_votos_por_sessao(sessao_id)
        sim = contagem.get("SIM", 0)
        nao = contagem.get("NAO", 0)
        resultado = "APROVADA" if sim > nao else ("REJEITADA" if nao > sim else "EMPATE")
        await publicar_resultado_votacao({
            "pauta_id": sessao.pauta_id,
            "sessao_id": sessao.id,
            "sim": sim,
            "nao": nao,
            "resultado": resultado,
        })

        logger.info("Sessão encerrada manualmente.", extra={"event": "session_closed_manual", "sessao_id": sessao_id})
        return sessao
