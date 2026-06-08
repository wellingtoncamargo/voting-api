from datetime import datetime
from typing import Optional, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ── Paginação ────────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    limit: int


# ── Pauta ────────────────────────────────────────────────────────────────────

class PautaCreateRequest(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=255,
                        examples=["Aprovação de orçamento anual"])
    descricao: Optional[str] = Field(None, max_length=1000,
                                     examples=["Votação sobre o orçamento do próximo ano."])


class PautaUpdateRequest(BaseModel):
    titulo: Optional[str] = Field(None, min_length=1, max_length=255,
                                  examples=["Novo título da pauta"])
    descricao: Optional[str] = Field(None, max_length=1000,
                                     examples=["Nova descrição"])


class PautaResponse(BaseModel):
    id: str
    titulo: str
    descricao: Optional[str] = None
    created_at: datetime


# ── Sessão ───────────────────────────────────────────────────────────────────

class SessaoCreateRequest(BaseModel):
    duracao_segundos: Optional[int] = Field(None, ge=1, examples=[300])


class SessaoResponse(BaseModel):
    id: str
    pauta_id: str
    inicio: datetime
    fim: datetime
    status: str


# ── Associado ────────────────────────────────────────────────────────────────

class AssociadoCreateRequest(BaseModel):
    cpf: str = Field(
        ...,
        min_length=11,
        max_length=11,
        pattern=r"^\d{11}$",
        examples=["52998224725"],
    )


class AssociadoResponse(BaseModel):
    id: str
    cpf: str
    created_at: datetime


# ── Voto ─────────────────────────────────────────────────────────────────────

class VotoCreateRequest(BaseModel):
    sessao_id: str = Field(..., examples=["uuid-da-sessao"])
    associado_id: str = Field(..., examples=["uuid-do-associado"])
    voto: str = Field(..., pattern=r"^(SIM|NAO)$", examples=["SIM"])


class VotoResponse(BaseModel):
    id: str
    sessao_id: str
    associado_id: str
    voto: str
    created_at: datetime


# ── Resultado ────────────────────────────────────────────────────────────────

class ResultadoResponse(BaseModel):
    sim: int
    nao: int
    resultado: str


# ── Validação CPF ────────────────────────────────────────────────────────────

class CpfValidacaoResponse(BaseModel):
    cpf: str
    valido: bool
    mensagem: str
