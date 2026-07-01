from fastapi import APIRouter, HTTPException, status

from app.api.v1.schemas import AssociadoResponse, TokenRequest, TokenResponse
from app.core.security import gerar_token_bearer
from app.infrastructure.repositories.associado_repository import AssociadoRepository

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/token", response_model=TokenResponse, summary="Gerar bearer token a partir do CPF")
async def gerar_token(body: TokenRequest):
    associado = await AssociadoRepository().buscar_por_cpf(body.cpf)
    if not associado:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="CPF não autenticado.")

    token = gerar_token_bearer(associado.cpf, associado.role.value)
    return TokenResponse(
        access_token=token,
        associado=AssociadoResponse(
            id=associado.id,
            cpf=associado.cpf,
            role=associado.role,
            created_at=associado.created_at,
        ),
    )
