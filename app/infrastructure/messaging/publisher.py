import json
import logging
import aio_pika
from app.core.config import settings

logger = logging.getLogger(__name__)

QUEUE_NAME = "voting-results"


async def publicar_resultado_votacao(payload: dict) -> None:
    """
    Publica o resultado de uma votação na fila RabbitMQ.
    Falhas de conexão são logadas mas não propagadas para não afetar o fluxo principal.
    """
    try:
        connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(QUEUE_NAME, durable=True)
            message = aio_pika.Message(
                body=json.dumps(payload).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )
            await channel.default_exchange.publish(message, routing_key=queue.name)
            logger.info(
                "Resultado publicado na fila.",
                extra={"event": "voting_result_published", "pauta_id": payload.get("pauta_id")},
            )
    except Exception as exc:
        logger.error(
            "Falha ao publicar resultado na fila RabbitMQ.",
            extra={"event": "rabbitmq_publish_error", "error": str(exc)},
        )
