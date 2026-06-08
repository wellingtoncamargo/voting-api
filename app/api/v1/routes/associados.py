from fastapi import APIRouter, Query

from app.api.v1.schemas import (
    AssociadoCreateRequest,
    AssociadoResponse,
    CpfValidacaoResponse,
    PaginatedResponse,
)
from app.application.use_cases.cadastrar_associado import CadastrarAssociadoUseCase
from app.application.use_cases.deletar_associado import DeletarAssociadoUseCase
from app.application.use_cases.listar_associados import ListarAssociadosUseCase
from app.domain.exceptions.exceptions import AssociadoNaoEncontradoError
from app.infrastructure.external.voter_validation_client import (
    VoterValidationClient,
    _cpf_matematicamente_valido,
)
from app.infrastructure.repositories.associado_repository import AssociadoRepository

router = APIRouter(prefix="/associados", tags=["Associados"])


@router.get(
    "",
    response_model=PaginatedResponse[AssociadoResponse],
    summary="Listar todos os associados",
)
async def listar_associados(
    page: int = Query(1, ge=1, description="Número da página"),
    limit: int = Query(20, ge=1, le=100, description="Itens por página"),
):
    uc = ListarAssociadosUseCase(repo=AssociadoRepository())
    result = await uc.executar(page=page, limit=limit)
    return PaginatedResponse(
        items=[AssociadoResponse(id=a.id, cpf=a.cpf, created_at=a.created_at) for a in result.items],
        total=result.total,
        page=result.page,
        limit=result.limit,
    )


@router.post(
    "",
    response_model=AssociadoResponse,
    status_code=201,
    summary="Cadastrar associado (valida CPF matematicamente e opcionalmente via API externa)",
)
async def cadastrar_associado(body: AssociadoCreateRequest):
    uc = CadastrarAssociadoUseCase(repo=AssociadoRepository(), validator=VoterValidationClient())
    associado = await uc.executar(cpf=body.cpf)
    return AssociadoResponse(id=associado.id, cpf=associado.cpf, created_at=associado.created_at)


@router.get(
    "/validar-cpf/{cpf}",
    response_model=CpfValidacaoResponse,
    summary="Verificar se um CPF é matematicamente válido (não persiste dados)",
)
async def validar_cpf(cpf: str):
    """
    Endpoint utilitário para verificar se um CPF é matematicamente válido
    pelo algoritmo dos dígitos verificadores (módulo 11).
    Aceita CPF com ou sem máscara. Não realiza cadastro.
    """
    valido = _cpf_matematicamente_valido(cpf)
    return CpfValidacaoResponse(
        cpf=cpf,
        valido=valido,
        mensagem="CPF válido." if valido else "CPF inválido: dígitos verificadores incorretos.",
    )


@router.get(
    "/{associado_id}",
    response_model=AssociadoResponse,
    summary="Buscar associado por ID",
)
async def buscar_associado(associado_id: str):
    associado = await AssociadoRepository().buscar_por_id(associado_id)
    if not associado:
        raise AssociadoNaoEncontradoError(f"Associado {associado_id} não encontrado.")
    return AssociadoResponse(id=associado.id, cpf=associado.cpf, created_at=associado.created_at)


@router.delete(
    "/{associado_id}",
    status_code=204,
    summary="Remover associado",
)
async def deletar_associado(associado_id: str):
    uc = DeletarAssociadoUseCase(repo=AssociadoRepository())
    await uc.executar(associado_id=associado_id)
