import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.domain.entities.models import (
    Pauta,
    Sessao,
    Associado,
    Voto,
)

@pytest.fixture(scope="session", autouse=True)
async def init_db():

    client = AsyncIOMotorClient(
        "mongodb://localhost:27017"
    )

    await init_beanie(
        database=client.desafio_unicred_test,
        document_models=[
            Pauta,
            Sessao,
            Associado,
            Voto,
        ]
    )

    yield

    client.close()