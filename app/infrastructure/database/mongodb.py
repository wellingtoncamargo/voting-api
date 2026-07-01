import logging

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.domain.entities.models import Associado, Pauta, Sessao, Voto
from app.domain.entities.models import PerfilAssociado
from app.domain.exceptions.exceptions import CpfInvalidoError
from app.infrastructure.external.voter_validation_client import _cpf_matematicamente_valido
from app.infrastructure.repositories.associado_repository import AssociadoRepository

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None


async def connect_db() -> None:
    global _client
    logger.info("Conectando ao MongoDB...", extra={"event": "db_connect_start"})
    print("MONGODB_URL =", settings.MONGODB_URL)
    print("DB_NAME =", settings.MONGODB_DB_NAME)
    _client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=_client[settings.MONGODB_DB_NAME],
        document_models=[Pauta, Sessao, Associado, Voto],
    )
    await _bootstrap_initial_admin()
    logger.info("MongoDB conectado com sucesso.", extra={"event": "db_connect_ok"})


async def _bootstrap_initial_admin() -> None:
    cpf = settings.INITIAL_ADMIN_CPF
    if not cpf:
        logger.info("Bootstrap de admin inicial não configurado.", extra={"event": "initial_admin_bootstrap_skipped"})
        return

    if not _cpf_matematicamente_valido(cpf):
        raise CpfInvalidoError(f"CPF inicial de admin inválido: {cpf}")

    repo = AssociadoRepository()
    associado = await repo.buscar_por_cpf(cpf)
    if associado is None:
        associado = Associado.model_construct(cpf=cpf, role=PerfilAssociado.ADMIN)
        await repo.criar(associado)
        logger.info(
            "Admin inicial criado.",
            extra={"event": "initial_admin_created", "associado_id": associado.id, "cpf": cpf},
        )
        return

    if associado.role != PerfilAssociado.ADMIN:
        await repo.atualizar_perfil(associado, PerfilAssociado.ADMIN)
        logger.info(
            "Admin inicial promovido.",
            extra={"event": "initial_admin_promoted", "associado_id": associado.id, "cpf": cpf},
        )
        return

    logger.info(
        "Admin inicial já existente.",
        extra={"event": "initial_admin_present", "associado_id": associado.id, "cpf": cpf},
    )


async def close_db() -> None:
    global _client
    if _client:
        _client.close()
    logger.info("Conexão com MongoDB encerrada.", extra={"event": "db_disconnect"})
