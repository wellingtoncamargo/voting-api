from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.domain.exceptions.exceptions import (
    AssociadoImpedidoError,
    AssociadoJaCadastradoError,
    AssociadoNaoEncontradoError,
    CpfInvalidoError,
    PautaNaoAtualizadaError,
    PautaNaoEncontradaError,
    SessaoEncerradaError,
    SessaoJaAtivaError,
    SessaoNaoEncontradaError,
    SessaoNaoPodeSerRemovidaError,
    VotoDuplicadoError,
)


def register_exception_handlers(app) -> None:
    @app.exception_handler(PautaNaoEncontradaError)
    async def _(r: Request, e: PautaNaoEncontradaError):
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(e)})

    @app.exception_handler(SessaoNaoEncontradaError)
    async def _(r: Request, e: SessaoNaoEncontradaError):
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(e)})

    @app.exception_handler(SessaoJaAtivaError)
    async def _(r: Request, e: SessaoJaAtivaError):
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(e)})

    @app.exception_handler(SessaoEncerradaError)
    async def _(r: Request, e: SessaoEncerradaError):
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(e)})

    @app.exception_handler(SessaoNaoPodeSerRemovidaError)
    async def _(r: Request, e: SessaoNaoPodeSerRemovidaError):
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(e)})

    @app.exception_handler(VotoDuplicadoError)
    async def _(r: Request, e: VotoDuplicadoError):
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(e)})

    @app.exception_handler(AssociadoNaoEncontradoError)
    async def _(r: Request, e: AssociadoNaoEncontradoError):
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(e)})

    @app.exception_handler(AssociadoJaCadastradoError)
    async def _(r: Request, e: AssociadoJaCadastradoError):
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(e)})

    @app.exception_handler(AssociadoImpedidoError)
    async def _(r: Request, e: AssociadoImpedidoError):
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": str(e)})

    @app.exception_handler(CpfInvalidoError)
    async def _(r: Request, e: CpfInvalidoError):
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": str(e)})

    @app.exception_handler(PautaNaoAtualizadaError)
    async def _(r: Request, e: PautaNaoAtualizadaError):
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(e)})
