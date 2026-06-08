from datetime import datetime
from enum import Enum
from typing import Optional
from beanie import Document
from pymongo import IndexModel, ASCENDING
from pydantic import Field
import uuid


class StatusSessao(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class VotoEnum(str, Enum):
    SIM = "SIM"
    NAO = "NAO"


class Pauta(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    titulo: str
    descricao: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "pautas"


class Sessao(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pauta_id: str
    inicio: datetime = Field(default_factory=datetime.now)
    fim: datetime
    status: StatusSessao = StatusSessao.OPEN

    class Settings:
        name = "sessoes"
        indexes = [
            IndexModel([("pauta_id", ASCENDING), ("status", ASCENDING)]),
            IndexModel([("fim", ASCENDING)]),
        ]


class Associado(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    cpf: str
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "associados"
        indexes = [
            IndexModel([("cpf", ASCENDING)], unique=True),
        ]


class Voto(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sessao_id: str
    associado_id: str
    voto: VotoEnum
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "votos"
        indexes = [
            IndexModel([("sessao_id", ASCENDING), ("associado_id", ASCENDING)], unique=True),
            IndexModel([("sessao_id", ASCENDING)]),
        ]
