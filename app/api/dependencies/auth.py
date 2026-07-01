from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decodificar_token_bearer
from app.domain.entities.models import Associado, PerfilAssociado
from app.domain.exceptions.exceptions import AutenticacaoInvalidaError, PermissaoNegadaError
from app.infrastructure.repositories.associado_repository import AssociadoRepository

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_associado(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> Associado:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token bearer ausente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decodificar_token_bearer(credentials.credentials)
    except AutenticacaoInvalidaError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    cpf = payload.get("sub")
    if not isinstance(cpf, str) or not cpf:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token bearer inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    associado = await AssociadoRepository().buscar_por_cpf(cpf)
    if not associado:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Associado não encontrado para o token informado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return associado


async def require_admin(current_associado: Associado = Depends(get_current_associado)) -> Associado:
    if current_associado.role != PerfilAssociado.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ação restrita a administradores.",
        )
    return current_associado

