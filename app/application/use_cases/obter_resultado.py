import logging

from app.domain.exceptions.exceptions import PautaNaoEncontradaError, SessaoNaoEncontradaError
from app.infrastructure.repositories.pauta_repository import PautaRepository
from app.infrastructure.repositories.sessao_repository import SessaoRepository
from app.infrastructure.repositories.voto_repository import VotoRepository

logger = logging.getLogger(__name__)


class ObterResultadoUseCase:
    def __init__(
        self,
        pauta_repo: PautaRepository,
        sessao_repo: SessaoRepository,
        voto_repo: VotoRepository,
    ):
        self._pauta_repo = pauta_repo
        self._sessao_repo = sessao_repo
        self._voto_repo = voto_repo

    async def executar(self, pauta_id: str) -> dict:
        pauta = await self._pauta_repo.buscar_por_id(pauta_id)
        if not pauta:
            raise PautaNaoEncontradaError(f"Pauta {pauta_id} não encontrada.")

        sessao = await self._sessao_repo.buscar_sessao_ativa_por_pauta(pauta_id)
        if not sessao:
            sessao = await self._sessao_repo.buscar_ultima_sessao_por_pauta(pauta_id)

        if not sessao:
            raise SessaoNaoEncontradaError(f"Nenhuma sessão encontrada para a pauta {pauta_id}.")

        contagem = await self._voto_repo.contar_votos_por_sessao(sessao.id)
        sim = contagem.get("SIM", 0)
        nao = contagem.get("NAO", 0)
        resultado = "APROVADA" if sim > nao else ("REJEITADA" if nao > sim else "EMPATE")

        logger.info(
            "Resultado calculado.",
            extra={
                "event": "result_calculated",
                "pauta_id": pauta_id,
                "sim": sim,
                "nao": nao,
                "resultado": resultado,
            },
        )
        return {"sim": sim, "nao": nao, "resultado": resultado}
