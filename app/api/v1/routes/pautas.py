from fastapi import APIRouter, Query

from app.api.v1.schemas import (
    PaginatedResponse,
    PautaCreateRequest,
    PautaResponse,
    PautaUpdateRequest,
    ResultadoResponse,
    SessaoCreateRequest,
    SessaoResponse,
)
from app.application.use_cases.abrir_sessao import AbrirSessaoUseCase
from app.application.use_cases.atualizar_pauta import AtualizarPautaUseCase
from app.application.use_cases.criar_pauta import CriarPautaUseCase
from app.application.use_cases.deletar_pauta import DeletarPautaUseCase
from app.application.use_cases.encerrar_sessao import EncerrarSessaoUseCase
from app.application.use_cases.listar_pautas import ListarPautasUseCase
from app.application.use_cases.listar_sessoes import ListarSessoesUseCase
from app.application.use_cases.obter_resultado import ObterResultadoUseCase
from app.infrastructure.repositories.pauta_repository import PautaRepository
from app.infrastructure.repositories.sessao_repository import SessaoRepository
from app.infrastructure.repositories.voto_repository import VotoRepository

router = APIRouter(prefix="/pautas", tags=["Pautas"])


# ── Pautas ───────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=PaginatedResponse[PautaResponse],
    summary="Listar todas as pautas",
)
async def listar_pautas(
    page: int = Query(1, ge=1, description="Número da página"),
    limit: int = Query(20, ge=1, le=100, description="Itens por página"),
):
    uc = ListarPautasUseCase(repo=PautaRepository())
    result = await uc.executar(page=page, limit=limit)
    return PaginatedResponse(
        items=[PautaResponse(id=p.id, titulo=p.titulo, descricao=p.descricao, created_at=p.created_at) for p in result.items],
        total=result.total,
        page=result.page,
        limit=result.limit,
    )


@router.post(
    "",
    response_model=PautaResponse,
    status_code=201,
    summary="Criar uma nova pauta",
)
async def criar_pauta(body: PautaCreateRequest):
    uc = CriarPautaUseCase(repo=PautaRepository())
    pauta = await uc.executar(titulo=body.titulo, descricao=body.descricao)
    return PautaResponse(id=pauta.id, titulo=pauta.titulo, descricao=pauta.descricao, created_at=pauta.created_at)


@router.get(
    "/{pauta_id}",
    response_model=PautaResponse,
    summary="Buscar pauta por ID",
)
async def buscar_pauta(pauta_id: str):
    from app.domain.exceptions.exceptions import PautaNaoEncontradaError
    pauta = await PautaRepository().buscar_por_id(pauta_id)
    if not pauta:
        raise PautaNaoEncontradaError(f"Pauta {pauta_id} não encontrada.")
    return PautaResponse(id=pauta.id, titulo=pauta.titulo, descricao=pauta.descricao, created_at=pauta.created_at)


@router.patch(
    "/{pauta_id}",
    response_model=PautaResponse,
    summary="Atualizar pauta (título e/ou descrição)",
)
async def atualizar_pauta(pauta_id: str, body: PautaUpdateRequest):
    uc = AtualizarPautaUseCase(repo=PautaRepository())
    pauta = await uc.executar(pauta_id=pauta_id, titulo=body.titulo, descricao=body.descricao)
    return PautaResponse(id=pauta.id, titulo=pauta.titulo, descricao=pauta.descricao, created_at=pauta.created_at)


@router.delete(
    "/{pauta_id}",
    status_code=204,
    summary="Remover pauta (somente sem sessão ativa)",
)
async def deletar_pauta(pauta_id: str):
    uc = DeletarPautaUseCase(repo=PautaRepository(), sessao_repo=SessaoRepository())
    await uc.executar(pauta_id=pauta_id)


# ── Sessões ──────────────────────────────────────────────────────────────────

@router.get(
    "/{pauta_id}/sessoes",
    response_model=PaginatedResponse[SessaoResponse],
    summary="Listar sessões de uma pauta",
)
async def listar_sessoes(
    pauta_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    uc = ListarSessoesUseCase(pauta_repo=PautaRepository(), sessao_repo=SessaoRepository())
    result = await uc.executar(pauta_id=pauta_id, page=page, limit=limit)
    return PaginatedResponse(
        items=[SessaoResponse(id=s.id, pauta_id=s.pauta_id, inicio=s.inicio, fim=s.fim, status=s.status) for s in result.items],
        total=result.total,
        page=result.page,
        limit=result.limit,
    )


@router.post(
    "/{pauta_id}/sessao",
    response_model=SessaoResponse,
    status_code=201,
    summary="Abrir sessão de votação em uma pauta",
)
async def abrir_sessao(pauta_id: str, body: SessaoCreateRequest):
    uc = AbrirSessaoUseCase(pauta_repo=PautaRepository(), sessao_repo=SessaoRepository())
    sessao = await uc.executar(pauta_id=pauta_id, duracao_segundos=body.duracao_segundos)
    return SessaoResponse(id=sessao.id, pauta_id=sessao.pauta_id, inicio=sessao.inicio, fim=sessao.fim, status=sessao.status)


@router.patch(
    "/{pauta_id}/sessao/{sessao_id}/encerrar",
    response_model=SessaoResponse,
    summary="Encerrar sessão manualmente",
)
async def encerrar_sessao(pauta_id: str, sessao_id: str):
    uc = EncerrarSessaoUseCase(sessao_repo=SessaoRepository(), voto_repo=VotoRepository())
    sessao = await uc.executar(sessao_id=sessao_id)
    return SessaoResponse(id=sessao.id, pauta_id=sessao.pauta_id, inicio=sessao.inicio, fim=sessao.fim, status=sessao.status)


@router.get(
    "/{pauta_id}/resultado",
    response_model=ResultadoResponse,
    summary="Obter resultado da votação de uma pauta",
)
async def obter_resultado(pauta_id: str):
    uc = ObterResultadoUseCase(
        pauta_repo=PautaRepository(),
        sessao_repo=SessaoRepository(),
        voto_repo=VotoRepository(),
    )
    return await uc.executar(pauta_id=pauta_id)
