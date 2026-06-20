import logging

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.domain.entities.models import Associado, Pauta, Sessao, Voto

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
    logger.info("MongoDB conectado com sucesso.", extra={"event": "db_connect_ok"})


async def close_db() -> None:
    global _client
    if _client:
        _client.close()
    logger.info("Conexão com MongoDB encerrada.", extra={"event": "db_disconnect"})
