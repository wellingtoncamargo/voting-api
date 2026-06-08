from fastapi import APIRouter, Query

from app.api.v1.schemas import PaginatedResponse, VotoCreateRequest, VotoResponse
from app.application.use_cases.listar_votos import ListarVotosUseCase
from app.application.use_cases.registrar_voto import RegistrarVotoUseCase
from app.domain.entities.models import VotoEnum
from app.infrastructure.repositories.associado_repository import AssociadoRepository
from app.infrastructure.repositories.sessao_repository import SessaoRepository
from app.infrastructure.repositories.voto_repository import VotoRepository

router = APIRouter(prefix="/votos", tags=["Votos"])


@router.get(
    "/sessao/{sessao_id}",
    response_model=PaginatedResponse[VotoResponse],
    summary="Listar votos de uma sessão",
)
async def listar_votos(
    sessao_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
):
    uc = ListarVotosUseCase(sessao_repo=SessaoRepository(), voto_repo=VotoRepository())
    result = await uc.executar(sessao_id=sessao_id, page=page, limit=limit)
    return PaginatedResponse(
        items=[VotoResponse(id=v.id, sessao_id=v.sessao_id, associado_id=v.associado_id, voto=v.voto, created_at=v.created_at) for v in result.items],
        total=result.total,
        page=result.page,
        limit=result.limit,
    )


@router.post(
    "",
    response_model=VotoResponse,
    status_code=201,
    summary="Registrar voto de um associado em uma sessão",
)
async def registrar_voto(body: VotoCreateRequest):
    uc = RegistrarVotoUseCase(
        sessao_repo=SessaoRepository(),
        voto_repo=VotoRepository(),
        associado_repo=AssociadoRepository(),
    )
    voto = await uc.executar(
        sessao_id=body.sessao_id,
        associado_id=body.associado_id,
        voto=VotoEnum(body.voto),
    )
    return VotoResponse(
        id=voto.id,
        sessao_id=voto.sessao_id,
        associado_id=voto.associado_id,
        voto=voto.voto,
        created_at=voto.created_at,
    )
