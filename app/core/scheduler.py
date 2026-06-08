import asyncio
import logging
from datetime import datetime, timezone

from app.core.config import settings
from app.domain.entities.models import Sessao, StatusSessao
from app.infrastructure.messaging.publisher import publicar_resultado_votacao
from app.infrastructure.repositories.sessao_repository import SessaoRepository
from app.infrastructure.repositories.voto_repository import VotoRepository

logger = logging.getLogger(__name__)

_scheduler_task: asyncio.Task | None = None


async def _fechar_sessoes_loop() -> None:
    sessao_repo = SessaoRepository()
    voto_repo = VotoRepository()

    while True:
        try:
            agora = datetime.now(tz=timezone.utc).replace(tzinfo=None)
            sessoes_expiradas = await Sessao.find(
                Sessao.status == StatusSessao.OPEN,
                Sessao.fim <= agora,
            ).to_list()

            for sessao in sessoes_expiradas:
                await sessao_repo.atualizar_status(sessao, StatusSessao.CLOSED)
                logger.info(
                    "Sessão encerrada pelo scheduler.",
                    extra={"event": "session_closed_by_scheduler", "sessao_id": sessao.id},
                )
                contagem = await voto_repo.contar_votos_por_sessao(sessao.id)
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

        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error(
                "Erro no scheduler de sessões.",
                extra={"event": "scheduler_error", "error": str(exc)},
            )

        await asyncio.sleep(settings.SESSION_CLOSE_INTERVAL_SECONDS)


def start_scheduler() -> None:
    global _scheduler_task
    _scheduler_task = asyncio.create_task(_fechar_sessoes_loop())
    logger.info("Scheduler de sessões iniciado.", extra={"event": "scheduler_started"})


def stop_scheduler() -> None:
    global _scheduler_task
    if _scheduler_task and not _scheduler_task.done():
        _scheduler_task.cancel()
        logger.info("Scheduler de sessões encerrado.", extra={"event": "scheduler_stopped"})
